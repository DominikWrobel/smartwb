import aiohttp
import asyncio
import async_timeout
import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SmartWBSensor(SensorEntity):
    """Representation of a SmartWB sensor."""

    def __init__(self, name, ip, port, attribute, unit, friendly_name, unique_id, device_name, icon=None):
        """Initialize the sensor."""
        self._name = name  # Sensor-specific name
        self._ip = ip
        self._port = port
        self._attribute = attribute
        self._unit = unit
        self._friendly_name = friendly_name  # Unique friendly name for each sensor
        self._icon = icon
        self._state = None
        self._attr_unique_id = f"{unique_id}_{self._attribute}"
        self._unique_id = unique_id  # Links the sensor to the device
        self._device_name = device_name  # The device name from config flow

        # Set proper unit for meter_reading sensor
        if self._attribute == "meterReading":
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_suggested_display_precision = 2
        else:
            self._unit = unit

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._attribute == "meterReading":
            return self._attr_native_unit_of_measurement
        return self._unit

    @property
    def device_info(self):
        """Return device information, ensuring all sensors are tied to the same device with the config name."""
        return {
            "identifiers": {(DOMAIN, self._unique_id)},  # This links to the single device
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._friendly_name  # Return the friendly name for the sensor

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._attribute == "vehicleState":
            return self._map_vehicle_state(self._state)
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self._attribute == "vehicleState":
            return self._get_vehicle_state_icon()
        return self._icon

    def _map_vehicle_state(self, value):
        """Map vehicle state codes to human-readable values."""
        mapper = {
            1: "Ready",
            2: "Connected",
            3: "Charging",
            5: "Error"
        }
        return mapper.get(value, "Unknown")

    def _get_vehicle_state_icon(self):
        """Return the icon based on the vehicle state."""
        state = self._map_vehicle_state(self._state)
        icon_mapper = {
            "Ready": "mdi:ev-station",
            "Connected": "mdi:car-connected",
            "Charging": "mdi:car-electric",
            "Error": "mdi:alert-circle",
            "Unknown": "mdi:help-circle"
        }
        return icon_mapper.get(state, "mdi:help-circle")

    async def async_update(self):
        """Fetch new state data for the sensor."""
        url = f"http://{self._ip}:{self._port}/getParameters"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            self._state = data["list"][0].get(self._attribute)
                        else:
                            _LOGGER.error(f"Error fetching data from {url}: HTTP status {response.status}")
                            self._state = None
        except aiohttp.ClientConnectorError as e:
            _LOGGER.error(f"Connection error for {url}: {e}")
            self._state = None
        except asyncio.TimeoutError:
            _LOGGER.error(f"Timeout error for {url}")
            self._state = None
        except Exception as e:
            _LOGGER.error(f"Unexpected error fetching data from {url}: {e}")
            self._state = None

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the SmartWB sensors."""
    ip = config_entry.data['ip_address']
    port = config_entry.data['port']
    device_name = config_entry.data['name']  # Device name from config flow
    unique_id = config_entry.unique_id

    # Test connection before setting up entities
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                async with session.get(f"http://{ip}:{port}/getParameters") as response:
                    if response.status != 200:
                        raise ConfigEntryNotReady(f"EVSE device returned status {response.status}")
    except aiohttp.ClientConnectorError as e:
        raise ConfigEntryNotReady(f"Failed to connect to EVSE device: {e}")
    except asyncio.TimeoutError:
        raise ConfigEntryNotReady("Connection to EVSE device timed out")

    # Create sensor entities
    sensors = [
        SmartWBSensor(f"{device_name}_actual_current", ip, port, "actualCurrent", "A", "Actual Current", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_actual_power", ip, port, "actualPower", "kW", "Actual Power", unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(f"{device_name}_duration", ip, port, "duration", "Minutes", "Duration", unique_id, device_name, "mdi:clock-time-eight-outline"),
        SmartWBSensor(f"{device_name}_vehicle_state", ip, port, "vehicleState", None, "Vehicle State", unique_id, device_name),
        SmartWBSensor(f"{device_name}_max_current", ip, port, "maxCurrent", "A", "Max Current", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_actual_current_ma", ip, port, "actualCurrentMA", "mA", "Actual Current (mA)", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_always_active", ip, port, "alwaysActive", None, "Always Active", unique_id, device_name, "mdi:clock-time-eight-outline"),
        SmartWBSensor(f"{device_name}_last_action_user", ip, port, "lastActionUser", None, "Last Action User", unique_id, device_name),
        SmartWBSensor(f"{device_name}_last_action_uid", ip, port, "lastActionUID", None, "Last Action UID", unique_id, device_name),
        SmartWBSensor(f"{device_name}_energy", ip, port, "energy", "kWh", "Energy", unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(f"{device_name}_mileage", ip, port, "mileage", "km", "Mileage", unique_id, device_name, "mdi:map-marker-distance"),
        SmartWBSensor(f"{device_name}_meter_reading", ip, port, "meterReading", "kWh", "Meter Reading", unique_id, device_name, "mdi:meter-electric"),
        SmartWBSensor(f"{device_name}_current_p1", ip, port, "currentP1", "A", "Current Phase 1", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_current_p2", ip, port, "currentP2", "A", "Current Phase 2", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_current_p3", ip, port, "currentP3", "A", "Current Phase 3", unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(f"{device_name}_voltage_p1", ip, port, "voltageP1", "V", "Voltage Phase 1", unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(f"{device_name}_voltage_p2", ip, port, "voltageP2", "V", "Voltage Phase 2", unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(f"{device_name}_voltage_p3", ip, port, "voltageP3", "V", "Voltage Phase 3", unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(f"{device_name}_use_meter", ip, port, "useMeter", None, "Use Meter", unique_id, device_name),
        SmartWBSensor(f"{device_name}_rfid_uid", ip, port, "RFIDUID", None, "RFID UID", unique_id, device_name)
    ]

    # Add the sensors
    async_add_entities(sensors, True)
