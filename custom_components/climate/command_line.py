"""
Adds support for generic thermostat units.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.generic_thermostat/
"""
import asyncio
import logging

import voluptuous as vol

import subprocess

from homeassistant.core import callback
from homeassistant.core import DOMAIN as HA_DOMAIN
from homeassistant.components.climate import (
    STATE_HEAT, STATE_COOL, ClimateDevice, PLATFORM_SCHEMA,
    ATTR_OPERATION_MODE, SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT, STATE_ON, STATE_OFF, ATTR_TEMPERATURE,
    CONF_NAME, ATTR_ENTITY_ID, SERVICE_TURN_ON, SERVICE_TURN_OFF)
from homeassistant.helpers import condition
from homeassistant.helpers.event import (
    async_track_state_change, async_track_time_interval)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = []

DEFAULT_TOLERANCE = 0.3
DEFAULT_NAME = 'Command Thermostat'

CONF_OFF = 'command_off'
CONF_HEATER = 'command_heater'
CONF_COOLER = 'command_cooler'
CONF_MIN_TEMP = 'min_temp'
CONF_MAX_TEMP = 'max_temp'
CONF_TARGET_TEMP = 'target_temp'
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_OFF): cv.string,
    vol.Optional(CONF_HEATER): cv.string,
    vol.Optional(CONF_COOLER): cv.string,
    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_TARGET_TEMP): vol.Coerce(float),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the generic thermostat platform."""
    name = config.get(CONF_NAME)
    command_off = config.get(CONF_OFF)
    command_heater = config.get(CONF_HEATER)
    command_cooler = config.get(CONF_COOLER)
    min_temp = config.get(CONF_MIN_TEMP)
    max_temp = config.get(CONF_MAX_TEMP)
    target_temp = config.get(CONF_TARGET_TEMP)

    async_add_devices([CommandThermostat(
        hass, name, command_off, command_heater, command_cooler,
        min_temp, max_temp, target_temp)])


class CommandThermostat(ClimateDevice, RestoreEntity):
    """Representation of a Generic Thermostat device."""

    def __init__(self, hass, name, command_off, command_heater, command_cooler,
        min_temp, max_temp, target_temp):
        """Initialize the thermostat."""
        self.hass = hass
        self._name = name
        self.command_off = command_off
        self.command_heater = command_heater
        self.command_cooler = command_cooler
        
        self._state = STATE_OFF

        self._active = False
        self._min_temp = min_temp
        self._max_temp = max_temp
        self._target_temp = target_temp
        self._unit = hass.config.units.temperature_unit

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Run when entity about to be added."""
        # Check If we have an old state
        old_state = yield from self.async_get_last_state()
        if old_state is not None:
            # If we have no initial temperature, restore
            if self._target_temp is None:
                self._target_temp = float(
                    old_state.attributes[ATTR_TEMPERATURE])

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    @property
    def name(self):
        """Return the name of the thermostat."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def current_temperature(self):
        """Return the sensor temperature."""
        return None

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        return self._state

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def operation_list(self):
        """List of available operation modes."""
        return [STATE_COOL, STATE_HEAT, STATE_OFF, STATE_ON]

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        if operation_mode == STATE_ON:
            operation_mode = STATE_HEAT # FIXME
            
        self._state = operation_mode

        self.call_command_for_state(self._state)
        
        self.schedule_update_ha_state()

    @asyncio.coroutine
    def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temp = temperature
        self.call_command_for_temperature( temperature )
        yield from self.async_update_ha_state()

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._min_temp:
            return self._min_temp

        return ClimateDevice.min_temp.fget(self)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._max_temp:
            return self._max_temp

        return ClimateDevice.max_temp.fget(self)

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return self._state != STATE_OFF

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @staticmethod
    def _switch(command):
        """Execute the actual commands."""
        _LOGGER.info("Running command: %s", command)

        success = (subprocess.call(command, shell=True) == 0)

        if not success:
            _LOGGER.error("Command failed: %s", command)

        return success
    
    def call_command_for_state(self, state):
        """Change the device's state."""
        if state == STATE_HEAT:
            CommandThermostat._switch(self.command_heater)
        elif state == STATE_COOL:
            CommandThermostat._switch(self.command_cooler)
        elif state == STATE_OFF:
            CommandThermostat._switch(self.command_off)
        else:
            _LOGGER.error('Unrecognized state: %s', state)
            
    def call_command_for_temperature(self, temp):
        _LOGGER.error('Method not implemented: temperature: %f', temp)
        
