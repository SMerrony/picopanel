# SPDX-License-Identifier: MIT

# Display-related...xxx
MATRIX_WIDTH = 64
MATRIX_HEIGHT = 64
CHAIN_WIDTH = 1  # Not chained
CHAIN_HEIGHT = 1 # Not stacked
BIT_DEPTH = 2    # This significantly affects performance and flicker

VERBOSE = True

BASE_TOPIC = "rgbmatrix/" # probably the same for all your displays
DISPLAY_ID = "2"          # unique per display

# Don't change these...
# 
URGENT_TOPIC = BASE_TOPIC + "urgent"
CONTROL_TOPIC = BASE_TOPIC + "control"+ DISPLAY_ID

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
