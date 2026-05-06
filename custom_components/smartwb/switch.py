import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SmartWB switch."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    ip = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["name"]
    unique_id = config_entry.unique_id

    switch = SmartWBSwitch(hass, coordinator, ip, port, config_entry.entry_id, unique_id, device_name)
    async_add_entities([switch])


class SmartWBSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SmartWB switch."""

    def __init__(self, hass, coordinator, ip, port, entry_id, unique_id, device_name):
        super().__init__(coordinator)
        self.hass = hass
        self._ip = ip
        self._port = port
        self._attr_unique_id = f"{unique_id}_switch"
        self._unique_id = unique_id
        self._device_name = device_name
        self._name = f"{device_name}_switch"

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._unique_id)}}

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        """Read switch state directly from shared coordinator data."""
        if self.coordinator.data is None:
            return None
        evse_state = self.coordinator.data.get("evseState")
        return evse_state == "true" or evse_state is True

    async def async_turn_on(self, **kwargs):
        await self._send_command("setStatus?active=true")

    async def async_turn_off(self, **kwargs):
        await self._send_command("setStatus?active=false")

    async def _send_command(self, command):
        """Send command to SmartWB, then refresh coordinator so all entities update."""
        url = f"http://{self._ip}:{self._port}/{command}"
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    response_text = await response.text()
                    if response_text.startswith("S0_"):
                        _LOGGER.info("SmartWB command OK: %s", response_text)
                    elif response_text.startswith("E0_"):
                        _LOGGER.error("SmartWB internal error: %s", response_text)
                    elif response_text.startswith("E1_"):
                        _LOGGER.error("SmartWB invalid value: %s", response_text)
                    elif response_text.startswith("E2_"):
                        _LOGGER.error("SmartWB wrong parameter: %s", response_text)
                    elif response_text.startswith("E3_"):
                        _LOGGER.warning("SmartWB state unchanged: %s", response_text)
                    else:
                        _LOGGER.error("SmartWB unexpected response: %s", response_text)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout sending command to %s", url)
        except Exception as e:
            _LOGGER.error("Error sending command to %s: %s", url, e)

        # Refresh coordinator after command - this updates ALL entities at once
        await self.coordinator.async_request_refresh()
