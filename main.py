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
import traceback
import wifi

from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
# from adafruit_display_text.scrolling_label import ScrollingLabel
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from displayio import Bitmap

import constants

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width = constants.MATRIX_WIDTH * constants.CHAIN_WIDTH,
    height = constants.MATRIX_HEIGHT * constants.CHAIN_HEIGHT,
    bit_depth = constants.BIT_DEPTH,
    rgb_pins = [board.GP2, board.GP3, board.GP4, board.GP5, board.GP8, board.GP9],
    addr_pins = [board.GP10, board.GP16, board.GP18, board.GP20, board.GP22],
    clock_pin = board.GP11, 
    latch_pin = board.GP12, 
    output_enable_pin = board.GP13,
    tile = constants.CHAIN_HEIGHT, 
)
fb = framebufferio.FramebufferDisplay(matrix, auto_refresh=True)

display_group = displayio.Group()
empty_group = displayio.Group()
display_on = True

font_4_6 = bitmap_font.load_font("fonts/4x6.bdf", Bitmap)
font_3_5 = bitmap_font.load_font("fonts/tiny3x5.bdf", Bitmap)

# Don't change these...
BASE_TOPIC = os.getenv('MQTT_BASE_TOPIC')
URGENT_TOPIC = BASE_TOPIC + "urgent"
DISPLAY_TOPIC = BASE_TOPIC + "display"

# Customise these as you like...
TIME_TOPIC = BASE_TOPIC + "time_hhmm"
DATE_TOPIC = BASE_TOPIC + "time_date"
OFFTEMP_TOPIC = BASE_TOPIC + "office_temp"
OUTTEMP_TOPIC = BASE_TOPIC + "outside_temp"
GBPEUR_TOPIC = BASE_TOPIC + "gbpeur"

# No data for these...
# DUMMY1 = "dummy1"

info = {
    # MQTT        : [prefix, x, y, fg_col, font, scale]
    TIME_TOPIC    : ["", 3, 8, 0xffff00, "builtin", 2],
    DATE_TOPIC    : ["", 2, 22, 0xff44ff, "builtin", 1],
    OFFTEMP_TOPIC : ["", 9, 33, 0xff0000, "3x5", 1],
    OUTTEMP_TOPIC : ["°C / ", 27, 33, 0xff0000, "3x5", 1],
    GBPEUR_TOPIC  : ["", 8, 39, 0xff55ee, "3x5", 1],
    # DUMMY1        : ["1234567890123456", 0, 44, 0xffffff, "3x5", 1],
    URGENT_TOPIC  : ["", 0, 52, 0xffff00, "builtin", 2],
}

labels = {}
for key in info:
    d = info[key]
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
    client.subscribe(DISPLAY_TOPIC)
    for key in info:
        print("DEBUG: About to subscribe to: >>>" + key + "<<<")
        client.subscribe(key, 0)

def subscribed_cb(client, userdata, topic, granted_qos):
    print('DEBUG: Subscribed to {0} with QOS level {1}'.format(topic, granted_qos))

def message_cb(client, topic, message):
    global display_on
    if constants.VERBOSE:
        print("DEBUG: MQTT got topic: {0}, payload: {1}".format(topic, message))
    if topic in labels:
        labels[topic].text = info[topic][0] + message
    elif topic == DISPLAY_TOPIC:
        if message == "Off":
            display_on = False
            fb.show(empty_group)
        elif message == "On":
            display_on = True
            fb.show(display_group)
        else:
            print("WARNING: Unknow display control message: " + message)
    else:
        return
    gc.collect()
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
      if labels[URGENT_TOPIC].text != "":
         if blink_state:
               labels[URGENT_TOPIC].color = 0
               fb.show(display_group)
         else:
               labels[URGENT_TOPIC].color = info[URGENT_TOPIC][3]
               fb.show(display_group)
      time.sleep(1.0)

except Exception as e:
    print("ERROR:\n", str(e))
    print("Resetting in 10 seconds...")
    time.sleep(10)
    microcontroller.reset()
    