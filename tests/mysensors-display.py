"""
    Testing "gatewayserial.ino" at examples folder

    Dep:
        - https://github.com/theolind/pymysensors
        - pip3 install pymysensors)


    Raw commands using mysensors serial API
        (https://www.mysensors.org/download/serial_api_20)

    DISPLAY_OFF: 0;1;1;0;47;10
    DISPLAY_ON: 0;1;1;0;47;11
    CURSOR_OFF: 0;1;1;0;47;20

"""

import mysensors.mysensors as mysensors
import time
import sys

SERIAL_PORT="/dev/ttyUSB0"

DISPLAY_CLEAR = '30'
DISPLAY_ON  = '11'
DISPLAY_OFF  = '10'
BACKLIGHT = '1'      # + 1 byte (1 .. 8)
CURSOR_ON = '21'
CURSOR_OFF = '20'
BLINK_CURSOR_ON = '40'
BLINK_CURSOR_OFF = '41'


def event_callback(msg):
    """Callback for mysensors updates."""

    print('MSG | '\
        ' NodeId: {} | ChildId: {}  | Type:{}'.format(
            msg.node_id,msg.child_id,msg.type)
        )

GATEWAY = mysensors.SerialGateway(
    port = SERIAL_PORT,
    baud = 115200,
    event_callback = event_callback,
    protocol_version='2.2')


GATEWAY.start()
# To set sensor 1, child 1, sub-type V_LIGHT (= 2), with value 1.

print("Wait for gateway ...")
time.sleep(2)
print("Sensors detected: {}".format(len(GATEWAY.sensors)))

is_sensor = GATEWAY.is_sensor(0,1)
# Check if there is a sensor
print('Check for a valid sensor at node 0 child 1: {}'.format(is_sensor))


### Start Test

print("Clear Screen ...")
GATEWAY.set_child_value(0, 1, 47, DISPLAY_CLEAR)
time.sleep(2)

print("Display OFF ...")
GATEWAY.set_child_value(0, 1, 47, DISPLAY_OFF)
time.sleep(2)

print("Display ON ...")
GATEWAY.set_child_value(0, 1, 47, DISPLAY_ON)
time.sleep(2)

print("Set BACKLIGHT 0 ...")
GATEWAY.set_child_value(0, 1, 47, BACKLIGHT + '0')
time.sleep(2)

print("Set BACKLIGHT 1 ...")
GATEWAY.set_child_value(0, 1, 47, BACKLIGHT + '1')
time.sleep(2)


print("Set BACKLIGHT 5 ...")
GATEWAY.set_child_value(0, 1, 47, BACKLIGHT + '5')
time.sleep(2)


col = 0
counter = 0
while True:
    time.sleep(1)
    counter = counter + 1

    print("Set CURSOR_OFF ")
    GATEWAY.set_child_value(0, 1, 47, CURSOR_OFF)
    GATEWAY.set_child_value(0, 1, 47, BLINK_CURSOR_OFF)
    time.sleep(2)


    print("Send Hello at row 0 col 0")
    GATEWAY.set_child_value(0, 1, 47, "AAHello at line 1")

    print("Send text to row 1 col 1")
    GATEWAY.set_child_value(0, 1, 47, "BBRow 2")
    print("Send counter to row 2 col 10")
    GATEWAY.set_child_value(0, 1, 47, "KCCount:{}".format(counter))

    print("Moving text")
    text = chr(ord('A') + col) + 'D <move> '
    GATEWAY.set_child_value(0, 1, 47, text)

    time.sleep(2)
    print("Set CURSOR_ON ")
    GATEWAY.set_child_value(0, 1, 47, CURSOR_ON)



    if col < 10:
        col = col +1
    else:
        col = 0
        time.sleep(5) # Wait before clear screen @BUG
        print("Clear screen")
        GATEWAY.set_child_value(0, 1, 47, DISPLAY_CLEAR)







