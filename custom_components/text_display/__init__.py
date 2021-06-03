""" LCD Text display integration
   @ TODO: Verify valids CMDS for service

"""
import asyncio
import logging
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import CONF_NAME

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.entity import ToggleEntity
from homeassistant.helpers.config_validation import (
    PLATFORM_SCHEMA, PLATFORM_SCHEMA_BASE)
from homeassistant.helpers.event import track_time_interval

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery

from homeassistant.const import (
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    SERVICE_TOGGLE,
    STATE_ON,
    STATE_OFF,
    ATTR_ENTITY_ID,
    DEVICE_DEFAULT_NAME
    )

from .const import CONF_ROWS,CONF_COLS,DOMAIN

DOMAIN="text_display"
_LOGGER = logging.getLogger(__name__)



SCAN_INTERVAL = timedelta(seconds = 60)

# Default SCHEME
DEFAULT_NAME = 'Text LCD display'
DEFAULT_ROWS = 0
DEFAULT_COLS = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default = DEFAULT_NAME): cv.string,
    vol.Optional(CONF_ROWS, default = DEFAULT_ROWS): cv.positive_int,
    vol.Optional(CONF_COLS, default = DEFAULT_COLS): cv.positive_int,
})


# Service definitions
SERVICE_BACKLIGHT = 'backlight'
SERVICE_WRITE_TEXT = 'write_text'
SERVICE_COMMAND = 'command'

ATTR_BRIGHTNESS = 'brightness'
ATTR_TEXT = 'text'
ATTR_COL = 'col'
ATTR_ROW = 'row'
ATTR_CMD = 'cmd'

CMD_CLEAR = 'clear'
CMD_BLINK_ON = 'blink_on'
CMD_BLINK_OFF = 'blink_off'
CMD_CURSOR_ON = 'cursor_on'
CMD_CURSOR_OFF = 'cursor_off'

# Service call validation schemas

DISPLAY_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

DISPLAY_BRIGHTNESS_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_BRIGHTNESS): cv.positive_int,
})

WRITE_TEXT_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_TEXT): cv.string,
    vol.Optional(ATTR_COL): cv.positive_int,
    vol.Optional(ATTR_ROW): cv.positive_int
})

COMMAND_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): cv.entity_ids,
    vol.Required(ATTR_CMD): cv.string
})


async def async_setup(hass, config):
    """ Setup displays """

    component = EntityComponent(_LOGGER, DOMAIN, hass, SCAN_INTERVAL)
    await component.async_setup(config)

    async def async_handle_display_service(service_call):
        """Handle calls to the display services."""
        targets = await component.async_extract_from_service(service_call)

        update_tasks = []
        for display in targets:
            if service_call.service == SERVICE_BACKLIGHT:
                brightness = service.data.get(ATTR_BRIGHTNESS)
                display.set_backlight(brightness)
                _LOGGER.info('Changed brightness to %s on display' % brightness)
            elif service_call.service == SERVICE_TURN_ON:
                display.turn_on()
                _LOGGER.info('Display turned on')
            elif service_call.service == SERVICE_TURN_OFF:
                display.turn_off()
                _LOGGER.info('Display turned off')
            elif service_call.service == SERVICE_TOGGLE:
                display.async_toggle()
                _LOGGER.info('Display toggle')
            elif service_call.service == SERVICE_COMMAND:
                cmd = service_call.data.get(ATTR_CMD)
                display.command(cmd)
            elif service_call.service == SERVICE_WRITE_TEXT:
                col = service_call.data.get(ATTR_COL) or 0
                row = service_call.data.get(ATTR_ROW) or 0
                text = service_call.data.get(ATTR_TEXT)
                display.set_cursor(row,col)
                display.write(text)
                _LOGGER.debug('Writting text to display')
            else:
                _LOGGER.info('Display turned off')

            if not display.should_poll:
                continue

            update_tasks.append(display.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    hass.services.async_register(
        DOMAIN, SERVICE_TURN_OFF, async_handle_display_service,
        schema=DISPLAY_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TURN_ON, async_handle_display_service,
        schema=DISPLAY_SERVICE_SCHEMA)
    hass.services.async_register(
        DOMAIN, SERVICE_TOGGLE, async_handle_display_service,
        schema=DISPLAY_SERVICE_SCHEMA)

    hass.services.async_register(
        DOMAIN, SERVICE_BACKLIGHT, async_handle_display_service,
        schema=DISPLAY_BRIGHTNESS_SCHEMA)

    hass.services.async_register(
        DOMAIN, SERVICE_WRITE_TEXT, async_handle_display_service,
        schema=WRITE_TEXT_SCHEMA)

    hass.services.async_register(
        DOMAIN, SERVICE_COMMAND, async_handle_display_service,
        schema=COMMAND_SCHEMA)

    return True




class TextDisplay(ToggleEntity):
    """ Interface for LCD text displays """

    def __init__(self,config):
        """ Init class """
        self._state = STATE_ON
        self._name = config.get(CONF_NAME)
        self._rows = config.get(CONF_ROWS)
        self._cols = config.get(CONF_COLS)
        self._screen_on = True
        self._backlight = 8 # valid 1 .. 8

    @property
    def should_poll(self):
        """Screen cannot be polled"""
        return False

    @property
    def name(self):
        """Return the name. """
        return self._name

    @property
    def icon(self):
        """Return the icon to use for device if any."""
        return 'mdi:airplay'

    @property
    def state(self):
        """Return the state of the display."""
        return self._state

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self):
        """Turn the display on."""
        self.display_on()
        self.set_backlight(self._backlight)
        self._state = STATE_ON
        self.schedule_update_ha_state()

    def turn_off(self):
        """Turn the display off."""
        self.set_backlight(1)
        self.display_off()
        self._state = STATE_OFF
        self.schedule_update_ha_state()

    def command(self,cmd):
        """ Redirect extra commands """
        if cmd == CMD_CLEAR:
            self.clear()
        elif cmd == CMD_CURSOR_ON:
            self.enable_cursor(True)
        elif cmd == CMD_CURSOR_OFF:
            self.enable_cursor(False)
        elif cmd == CMD_BLINK_ON:
            self.blink_cursor(True)
        elif cmd == CMD_BLINK_OFF:
            self.blink_cursor(False)



    def set_backlight(self,n):
        """Set backlight 1 .. 8"""
        raise NotImplementedError()

    def display_on(self):
        """ Screen on """
        raise NotImplementedError()

    def display_off(self):
        """ Screen off """
        raise NotImplementedError()


    def clear(self):
        """ Clear screen and set the cursos position to upper-left """
        raise NotImplementedError()

    def set_cursor(self,row = 0, col = 0):
        """ Set the cursor position, rows starts at 0 """
        raise NotImplementedError()

    def enable_cursor(self,enable = True):
        """ Enable/Disable cursor """
        raise NotImplementedError()

    def blink_cursor(self,enable = True):
        """ Enable/Disable cursor blink """
        raise NotImplementedError()


    def scroll(self,direction = 'left'):
        """ Scroll text """
        raise NotImplementedError()


    def write(self,ascii_txt):
        """Write some text at position"""
        self._write(ascii_txt.encode('ASCII'))



