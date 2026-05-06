import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


class SmartWBCoordinator(DataUpdateCoordinator):
    """Single coordinator that fetches data once for all entities."""

    def __init__(self, hass: HomeAssistant, ip: str, port: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self._ip = ip
        self._port = port

    async def _async_update_data(self):
        """Fetch data from the EVSE device - called once per interval for ALL entities."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        session = async_get_clientsession(self.hass)
        try:
            async with asyncio.timeout(10):
                async with session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"EVSE returned HTTP {response.status}")
                    data = await response.json()
                    return data["list"][0]
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout connecting to EVSE device") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except (KeyError, IndexError) as err:
            raise UpdateFailed(f"Unexpected data format: {err}") from err


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up SmartWB integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    ip = config_entry.data["ip_address"]
    port = config_entry.data["port"]

    coordinator = SmartWBCoordinator(hass, ip, port)
    # Initial fetch - raises ConfigEntryNotReady automatically on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][config_entry.entry_id] = {
        "coordinator": coordinator,
        "config": config_entry.data,
    }

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, config_entry.unique_id)},
        name=config_entry.data.get("name"),
        manufacturer="SmartWB",
        model="SimpleEVSE-WiFi",
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
