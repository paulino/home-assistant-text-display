""" Support for LCD Text display through my sensors gateway. """

import asyncio
import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.components.mysensors.const import MYSENSORS_GATEWAYS
from homeassistant.components.mysensors.const import DOMAIN as MYSENSORS_DOMAIN

from custom_components.text_display import PLATFORM_SCHEMA
from custom_components.text_display import TextDisplay
from custom_components.text_display.const import (CONF_ROWS,CONF_COLS)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'MySensors LCD Display '

CONF_NODE_ID = 'node_id'
CONF_CHILD_ID = 'child_id'

V_TEXT = 47 # Mysensors constant

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NODE_ID): cv.positive_int,
    vol.Required(CONF_CHILD_ID): cv.positive_int
})

LCD_DISPLAY_ON = '01'
LCD_DISPLAY_OFF = '00'
LCD_BACKLIGHT = '1'      # + 1 byte (1 .. 8)
LCD_CURSOR_ON = '21'
LCD_CURSOR_OFF = '20'
LCD_CLEAR_SCREEN = '30'
LCD_BLINK_CURSOR_ON = '41'
LCD_BLINK_CURSOR_OFF = '40'


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):

    async def wait_mysensors():
        """ Poll until a mysensors gateway is set """        
        tries = 1
        gateways = {}
        while tries <= 10:
            _LOGGER.info('Wait for MySensors gateway {}/10'.format(tries))
            tries = tries +1
            if MYSENSORS_GATEWAYS in hass.data[MYSENSORS_DOMAIN] and\
                     len(hass.data[MYSENSORS_DOMAIN][MYSENSORS_GATEWAYS]) > 0 :
                gateways = hass.data[MYSENSORS_DOMAIN].get(MYSENSORS_GATEWAYS)
                break
            await asyncio.sleep(10)
        else:
            _LOGGER.error('MySensors gateway not found')
            return False

        if len(gateways) > 1:
            _LOGGER.warning('Found multiple mysensors gateways, taking only using fist')

        if len(gateways) >= 1:
            gateway_id = next(iter(gateways.keys()))
            _LOGGER.info('MySensors gateway detected, using gw_id = {}'.format(gateway_id))
            gateways = hass.data[MYSENSORS_DOMAIN].get(MYSENSORS_GATEWAYS)
            gateway = gateways.get(gateway_id)            
            # Wait for gateway Initialization
            while not gateway.sensors:
             await asyncio.sleep(1)

            async_add_entities([TextDisplayMysensors(config,gateway)])
        return False

    # Wait until a mysensors gateway is initializated
    hass.async_create_task(wait_mysensors())

    return True

class TextDisplayMysensors(TextDisplay):
    """ Serial MySensors controller """

    def __init__(self,config,gateway):
        """ Init class """
        TextDisplay.__init__(self,config)
        self._node_id = config.get(CONF_NODE_ID)
        self._child_id = config.get(CONF_CHILD_ID)
        self._gateway = gateway
        self._cursor_position = 'AA'

        # Initialization
        self.clear()
        self.write('HomeAssistant')
        self.enable_cursor(False)
        self.blink_cursor(False)



    def set_backlight(self,n):
        """ m -- valid values 1 to 8  """
        self._write(LCD_BACKLIGHT + chr(ord('0')+n))

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
        """ Set the cursor position. Cursor position is static """
        _LOGGER.debug('Setting cursor to row %d, col %d' % (row,col))
        s_col = ord('A') + col
        s_row = ord('A') + row

        # This mus be send before write_text
        self._cursor_position = chr(s_col) + chr(s_row)

    def enable_cursor(self,enable = True):
        """ Enable/Disable cursor """
        if enable:
            self._write(LCD_CURSOR_ON)
        else:
            self._write(LCD_CURSOR_OFF)

    def blink_cursor(self,enable = True):
        """ Enable/Disable cursor blink """
        if enable:
            self._write(LCD_BLINK_CURSOR_ON)
        else:
            self._write(LCD_BLINK_CURSOR_OFF)


    def write(self,ascii_txt):
        """ Write some text at static position
            Warning: max payload in MySensors is 25bytes
        """
        text = self._cursor_position + ascii_txt
        self._write(text[:25])


    def _write(self,data):
        """ Send raw data using mysensors gateway """
        if self._gateway:
            if not self._gateway.is_sensor(self._node_id,self._child_id):
                _LOGGER.error('The sensor is not a MySensors sensor')
            else:
                self._gateway.set_child_value(self._node_id, self._child_id, V_TEXT, data)
        return



