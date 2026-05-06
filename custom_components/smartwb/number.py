import asyncio
import logging

import aiohttp
import async_timeout
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class EVSECurrentSlider(CoordinatorEntity, NumberEntity):
    """Representation of an EVSE current slider."""

    def __init__(self, coordinator, ip, port, name, unique_id, device_name):
        super().__init__(coordinator)
        self._ip = ip
        self._port = port
        self._attr_unique_id = f"{unique_id}_slider"
        self._unique_id = unique_id
        self._device_name = device_name
        self._name = name
        self._attr_native_unit_of_measurement = "A"
        self._attr_native_min_value = 6
        self._attr_native_step = 1

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": "SmartWB",
            "model": "SimpleEVSE-WiFi",
        }

    @property
    def name(self):
        return self._name

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("actualCurrent")

    @property
    def native_max_value(self):
        if self.coordinator.data is None:
            return 32
        return self.coordinator.data.get("maxCurrent", 32)

    async def async_set_native_value(self, value):
        """Set the current value and refresh coordinator."""
        current_a = int(value)
        url = f"http://{self._ip}:{self._port}/setCurrent?current={current_a}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            if response_text.startswith("S0_"):
                                _LOGGER.info("Successfully set current to %sA", value)
                            elif response_text.startswith("E0_"):
                                _LOGGER.error("Could not set current - internal error")
                                return
                            elif response_text.startswith("E1_"):
                                _LOGGER.error("Could not set current - value out of range")
                                return
                            elif response_text.startswith("E2_"):
                                _LOGGER.error("Could not set current - wrong parameter")
                                return
                            else:
                                _LOGGER.error("Unexpected response: %s", response_text)
                                return
                        else:
                            _LOGGER.error("Error setting current: HTTP %s", response.status)
                            return
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error("Connection error setting current: %s", e)
            return
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error setting current")
            return
        except Exception as e:
            _LOGGER.error("Unexpected error setting current: %s", e)
            return

        # Refresh coordinator after successful command
        await self.coordinator.async_request_refresh()


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the EVSE number entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    ip = config_entry.data["ip_address"]
    port = config_entry.data["port"]
    device_name = config_entry.data["name"]
    unique_id = config_entry.unique_id

    slider = EVSECurrentSlider(
        coordinator, ip, port, f"{device_name} Set Current", unique_id, device_name
    )
    async_add_entities([slider])
