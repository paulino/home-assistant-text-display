""" Controller for a serial display connected to a serial port ""

    Tested with:
    - Display NHD-0420D3Z, Newhaven Display International, Inc.
      http://www.newhavendisplay.com/specs/NHD-0420D3Z-FL-GBW-V3.pdf

"""
import asyncio
import logging
import serial

import voluptuous as vol

from homeassistant.helpers.entity import Entity

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_NAME,STATE_ON, STATE_OFF)

from custom_components.text_display import PLATFORM_SCHEMA
from custom_components.text_display import TextDisplay
from custom_components.text_display.const import (CONF_ROWS,CONF_COLS)

_LOGGER = logging.getLogger(__name__)


CONF_PORT = 'serial_port'
CONF_BAUDRATE = 'baudrate'

DEFAULT_NAME = 'Serial LCD Display'
DEFAULT_BAUDRATE = 9600
DEFAULT_ROWS = 4
DEFAULT_COLS = 20

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PORT): cv.string,
    vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
})

# LCD Commands from datasheet
LCD_SET_CONTRAST = b'\xfe\x52'  # + 1 byte (1 .. 50)
LCD_BACKLIGHT = b'\xfe\x53'     # + 1 byte (1 .. 8)
LCD_CLEAR_SCREEN = b'\xfe\x51'
LCD_DISPLAY_ON = b'\xfe\x41'
LCD_DISPLAY_OFF = b'\xfe\x42'
LCD_CURSOR_HOME = b'\xfe\x46' # Text is not altered
LCD_SET_CURSOR = b'\xfe\x45'  # + 1 byte. Line 1: 0x00, line 2:0x40,
                              # Line 3: 0x14, line 4:0x54

async def async_setup_platform(
    hass, config, async_add_devices, discovery_info=None):
    """Setup the serial display platform."""

    async_add_devices([TextDisplaySerial(config)])
    _LOGGER.info('Added serial display at port {}'.
                 format(config.get(CONF_PORT)))



class TextDisplaySerial(TextDisplay):
    """ Serial display controller """

    def __init__(self,config):
        """ Init class """
        TextDisplay.__init__(self,config)

        self._port = config.get(CONF_PORT)
        self._baudrate = config.get(CONF_BAUDRATE)
        self._backlight = 8
        self._permanent = False
        self._port_locked = False

        # Initialization
        self.clear()
        self.set_backlight(self._backlight)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name


    async def async_set_backlight(self,x):
        _LOGGER.info('x=%s' % x)

    def set_backlight(self,n):
        """ m -- valid values 1 to 8  """
        self._write(LCD_BACKLIGHT + chr(n).encode('ASCII'))

    def clear(self):
        """ Clear screen """
        self._write(LCD_CLEAR_SCREEN)

    def display_on(self):
        """ Screen on """
        self._write(LCD_DISPLAY_ON)

    def display_off(self):
        """ Screen off """
        self._write(LCD_DISPLAY_OFF)


    def set_cursor(self,row = 0,col = 0):
        """ Set the cursor position """
        pos = None
        _LOGGER.debug('Setting cursor to row %d, col %d' % (row,col))
        if row >= 0 and row <= 3:
            lines = [0x00,0x40,0x14,0x54]
            pos = lines[row] + col
        if pos != None:
            self._write(LCD_SET_CURSOR + chr(pos).encode('ASCII'))


    def _write(self,data):
        """ write raw chars """
        if self._port_locked:
            _LOGGER.error('This controller is not thread safe, this would must not happen')
            return
        self._port_locked = True
        if not self._permanent:
            conn = None
            conn = serial.Serial(self._port, self._baudrate)
            conn.write(data)
            conn.close()
        self._port_locked = False
        return


