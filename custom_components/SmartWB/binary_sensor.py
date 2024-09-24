from homeassistant.components.binary_sensor import BinarySensorEntity
import aiohttp
import async_timeout

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SmartWB binary sensors."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    name = config_entry.data['name']
    entry_id = config_entry.entry_id
    unique_id = config_entry.unique_id

    sensors = [
        SmartWBBinarySensor(f"{name}_smartwb_state", ip, port, "smartwbState", "SmartWB State", entry_id, unique_id)
    ]

    async_add_entities(sensors, True)

class SmartWBBinarySensor(BinarySensorEntity):
    """Representation of an SmartWB binary sensor."""

    def __init__(self, name, ip, port, attribute, friendly_name, entry_id, unique_id):
        """Initialize the binary sensor."""
        self._name = name
        self._ip = ip
        self._port = port
        self._attribute = attribute
        self._friendly_name = friendly_name
        self._state = None
        self._attr_unique_id = f"{unique_id}_{self._attribute}"
        self._entry_id = entry_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
        }

    @property
    def is_on(self):
        """Return true if the sensor is on."""
        return self._state == "1"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        data = await response.json()
                        self._state = data["list"][0].get(self._attribute)
        except Exception as e:
            self._state = None
            # Log the error in the Home Assistant log
            self.hass.components.logger.error(f"Error fetching data from {url}: {e}")
