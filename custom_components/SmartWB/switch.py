from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import asyncio
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SmartWB switch."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']

    switch = SmartWBSwitch(hass, f"{name}_switch", ip, port, config_entry.entry_id, config_entry.unique_id)
    async_add_entities([switch], True)

class EVSESwitch(SwitchEntity):
    """Representation of an SmartWB switch."""

    def __init__(self, hass, name, ip, port, entry_id, unique_id):
        """Initialize the switch."""
        self.hass = hass
        self._name = name
        self._ip = ip
        self._port = port
        self._state = None
        self._available = True
        self._unique_id = f"{unique_id}_switch"
        self._attr_extra_state_attributes = {}
        self._entry_id = entry_id

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
        }

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of the switch."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if the switch is on."""
        return self._state

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._send_command("setStatus?active=true")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._send_command("setStatus?active=false")

    async def _send_command(self, command):
        """Send command to SmartWB and update state."""
        url = f"http://{self._ip}:{self._port}/{command}"
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    response_text = await response.text()
                    if response_text.startswith("S0_"):
                        if "activated" in response_text.lower():
                            _LOGGER.info(f"SmartWB successfully activated: {response_text}")
                            self._state = True
                        elif "deactivated" in response_text.lower():
                            _LOGGER.info(f"SmartWB successfully deactivated: {response_text}")
                            self._state = False
                        else:
                            _LOGGER.info(f"SmartWB command successful, but state unclear: {response_text}")
                            self._state = "true" in command  # Fallback to the original logic
                    
                        self._available = True
                        self.async_write_ha_state()  # Immediately update the state
                    
                        # Schedule a delayed update to confirm the state
                        self.hass.loop.call_later(10, lambda: asyncio.create_task(self._delayed_update()))
                    elif response_text.startswith("E0_"):
                        _LOGGER.error(f"Internal error: {response_text}")
                        self._available = False
                    elif response_text.startswith("E1_"):
                        _LOGGER.error(f"Invalid value error: {response_text}")
                    elif response_text.startswith("E2_"):
                        _LOGGER.error(f"Wrong parameter error: {response_text}")
                    elif response_text.startswith("E3_"):
                        _LOGGER.warning(f"SmartWB state unchanged: {response_text}")
                        self._state = "activate" in response_text
                    else:
                        _LOGGER.error(f"Unexpected response: {response_text}")
                        self._available = False
        except asyncio.TimeoutError:
            self._available = False
            _LOGGER.error("Timeout error sending command to %s", url)
        except Exception as e:
            self._available = False
            _LOGGER.error("Error sending command to %s: %s", url, str(e))
    
        self.async_write_ha_state()

    async def _delayed_update(self):
        """Perform a delayed update to confirm the switch state."""
        await self.async_update()
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the switch."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    data = await response.json()
                    evse_state = data["list"][0].get("evseState")
                    new_state = evse_state == "true" or evse_state is True
                    if new_state != self._state:
                        _LOGGER.info(f"Switch state mismatch. Updated from {self._state} to {new_state}")
                        self._state = new_state
            self._available = True
        except asyncio.TimeoutError:
            self._available = False
            _LOGGER.error("Timeout error fetching data from %s", url)
        except Exception as e:
            self._available = False
            _LOGGER.error("Error fetching data from %s: %s", url, str(e))
