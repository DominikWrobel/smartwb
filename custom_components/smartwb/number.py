import aiohttp
import asyncio
import async_timeout
import logging
from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class EVSECurrentSlider(NumberEntity):
    """Representation of an EVSE current slider."""

    def __init__(self, name, ip, port, unique_id, device_name):
        """Initialize the current slider."""
        self._name = name
        self._ip = ip
        self._port = port
        self._value = None
        self._attr_unique_id = f"{unique_id}_slider"
        self._unique_id = unique_id  # Use this to link to the device
        self._device_name = device_name
        self._attr_native_max_value = 32  # Default max value, will be updated
        self._attr_native_unit_of_measurement = "A"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},
            "manufacturer": "SmartWB",
            "model": "SimpleEVSE-WiFi",
        }

    @property
    def name(self):
        """Return the name of the slider."""
        return self._name

    @property
    def native_value(self):
        """Return the current value of the slider."""
        return self._value

    @property
    def native_min_value(self):
        """Return the minimum value of the slider."""
        return 6

    @property
    def native_step(self):
        """Return the step value of the slider."""
        return 1

    async def async_set_native_value(self, value):
        """Set the current value of the slider."""
        current_a = int(value)
        url = f"http://{self._ip}:{self._port}/setCurrent?current={current_a}"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            response_text = await response.text()
                            if response_text.startswith("S0_"):
                                self._value = value
                                _LOGGER.info(f"Successfully set current to {value}A")
                            elif response_text.startswith("E0_"):
                                _LOGGER.error("Could not set current - internal error")
                            elif response_text.startswith("E1_"):
                                min_max = response_text.split("between ")[1].split(" and ")
                                _LOGGER.error(f"Could not set current - value must be between {min_max[0]}A and {min_max[1]}A")
                            elif response_text.startswith("E2_"):
                                _LOGGER.error("Could not set current - wrong parameter")
                            else:
                                _LOGGER.error(f"Unexpected response: {response_text}")
                        else:
                            _LOGGER.error(f"Error setting current: HTTP status {response.status}")
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error setting current: {e}")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout error setting current")
        except Exception as e:
            _LOGGER.error(f"Unexpected error setting current: {e}")

    async def async_update(self):
        """Fetch new state data for the slider."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data["type"] == "parameters" and len(data["list"]) > 0:
                                params = data["list"][0]
                                self._value = params.get("actualCurrent")
                                self._attr_native_max_value = params.get("maxCurrent", 32)
                            else:
                                _LOGGER.error(f"Unexpected data format from {url}")
                                self._value = None
                        else:
                            _LOGGER.error(f"Error fetching data from {url}: HTTP status {response.status}")
                            self._value = None
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error for {url}: {e}")
            self._value = None
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout error for {url}")
            self._value = None
        except Exception as e:
            _LOGGER.error(f"Unexpected error fetching data from {url}: {e}")
            self._value = None

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the EVSE number entities from a config entry."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    device_name = config_entry.data['name']
    unique_id = config_entry.unique_id

    # Add the current slider
    current_slider = EVSECurrentSlider(f"{device_name} Set Current", ip, port, unique_id, device_name)

    # Add the slider
    async_add_entities([current_slider], True)