# SPDX-FileCopyrightText: 2023 Stephen Merrony
# SPDX-License-Identifier: MIT

import board
import displayio
import framebufferio
import gc
import microcontroller
import os
import rgbmatrix
import socketpool
# import ssl
import terminalio
import time
import wifi

from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
# from adafruit_display_text.scrolling_label import ScrollingLabel
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from displayio import Bitmap

import config

CONFIG_FILENAME = "config.py" # used for reloading config below
PREV_FILENAME = CONFIG_FILENAME + ".old" # used for renaming the old version
NEW_FILENAME = CONFIG_FILENAME + ".new" # temp file for the new version

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width = config.MATRIX_WIDTH * config.CHAIN_WIDTH,
    height = config.MATRIX_HEIGHT * config.CHAIN_HEIGHT,
    bit_depth = config.BIT_DEPTH,
    rgb_pins = [board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9],
    addr_pins = [board.GP10, board.GP16, board.GP18, board.GP20, board.GP22],
    clock_pin = board.GP11, 
    latch_pin = board.GP12, 
    output_enable_pin = board.GP13,
    tile = config.CHAIN_HEIGHT, 
)
fb = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

display_group = displayio.Group()
empty_group = displayio.Group()
display_on = True

font_4_6 = bitmap_font.load_font("fonts/4x6.bdf", Bitmap)
font_3_5 = bitmap_font.load_font("fonts/tiny3x5.bdf", Bitmap)

labels = {}
for key in config.info:
    d = config.info[key]
    if d[4] == "builtin":
        t_font = terminalio.FONT
    elif d[4] == "3x5":
        t_font = font_3_5
    else:
        t_font = font_4_6
    labels[key] = Label(font=t_font, text=d[0], x=d[1], y=d[2], background_color=0, color=d[3], scale=d[5])
    display_group.append(labels[key])

fb.show(display_group)

def connected_cb(client, userdata, flags, rc):
    print("DEBUG: MQTT connected to broker")
    client.subscribe(config.CONTROL_TOPIC)
    for key in config.info:
        print("DEBUG: About to subscribe to: >>>" + key + "<<<")
        client.subscribe(key, 0)

def subscribed_cb(client, userdata, topic, granted_qos):
    print('DEBUG: Subscribed to {0} with QOS level {1}'.format(topic, granted_qos))

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def message_cb(client, topic, message):
    global display_on
    if config.VERBOSE:
        print("DEBUG: MQTT got topic: {0}, payload: {1}".format(topic, message))
    if topic in labels:
        labels[topic].text = config.info[topic][0] + message
    elif topic == config.CONTROL_TOPIC:
        if message == "Off":
            display_on = False
            fb.show(empty_group)
        elif message == "On":
            display_on = True
            fb.show(display_group)
        elif message.startswith("RECONFIGURE\n"):
            if not message.endswith("EOF\n"):
                print("WARNING: RECONFIGURE payload seems incomplete - ignoring")
            else:
                # N.B. various exceptions could be raised below, they will all be
                # handled by the main handler at the end of the program.
                print("INFO: Received complete RECONFIGURE message...")
                if NEW_FILENAME in os.listdir():
                    os.remove(NEW_FILENAME)
                conf_tmp =  open(NEW_FILENAME, "w")
                conf_tmp.write(remove_prefix(message[:-4], "RECONFIGURE\n"))
                conf_tmp.flush()
                conf_tmp.close()
                if PREV_FILENAME in os.listdir():
                    os.remove(PREV_FILENAME)
                os.rename(CONFIG_FILENAME, PREV_FILENAME)
                os.rename(NEW_FILENAME, CONFIG_FILENAME)
                os.sync()
                microcontroller.reset()
        else:
            print("WARNING: Unknown display control message: " + message)
    else:
        return
    if config.VERBOSE:
        print( "DEBUG: Pre-GC free memory : {} bytes".format(gc.mem_free()) ) 
    gc.collect()
    if config.VERBOSE:
        print( "DEBUG: Post-GC free memory: {} bytes".format(gc.mem_free()) )
    if display_on:
       fb.show(display_group)

try:
   while wifi.radio.ipv4_address == None:
      print("DEBUG: Connecting to WiFi")
      wifi.radio.connect(os.getenv('WIFI_SSID'), os.getenv('WIFI_PASSWORD'))
      time.sleep(1)
      
   print("DEBUG: WiFi connected")
   pool = socketpool.SocketPool(wifi.radio)
   mqtt_client = MQTT.MQTT (
      broker = os.getenv('MQTT_BROKER'),
      port = os.getenv('MQTT_PORT'),
      client_id = os.getenv('MQTT_CLIENT_ID'),
      username = os.getenv('MQTT_USERNAME'),
      password = os.getenv('MQTT_PASSWORD'),
      socket_pool = pool,
   )
   mqtt_client.on_connect = connected_cb
   mqtt_client.on_subscribe = subscribed_cb
   mqtt_client.on_message = message_cb

   print("Attempting to connect to %s" % mqtt_client.broker)
   mqtt_client.connect()

   blink_state = False
   while True:
      mqtt_client.loop()
      blink_state = not blink_state
      if labels[config.URGENT_TOPIC].text != "":
         if blink_state:
               labels[config.URGENT_TOPIC].color = 0
               fb.show(display_group)
         else:
               labels[config.URGENT_TOPIC].color = config.info[config.URGENT_TOPIC][3]
               fb.show(display_group)
      time.sleep(1.0)

except Exception as e:
    print("ERROR:\n", str(e))
    print("Resetting in 10 seconds...")
    time.sleep(10)
    microcontroller.reset()
    