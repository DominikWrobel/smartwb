import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartWBSensor(CoordinatorEntity, SensorEntity):
    """Representation of a SmartWB sensor backed by a shared coordinator."""

    def __init__(self, coordinator, attribute, unit, friendly_name, unique_id, device_name, icon=None):
        super().__init__(coordinator)
        self._attribute = attribute
        self._unit = unit
        self._friendly_name = friendly_name
        self._icon = icon
        self._attr_unique_id = f"{unique_id}_{attribute}"
        self._unique_id = unique_id
        self._device_name = device_name

        if self._attribute == "meterReading":
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL
            self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
            self._attr_suggested_display_precision = 2

    @property
    def device_info(self):
        return {"identifiers": {(DOMAIN, self._unique_id)}}

    @property
    def name(self):
        return self._friendly_name

    @property
    def native_unit_of_measurement(self):
        if self._attribute == "meterReading":
            return self._attr_native_unit_of_measurement
        return self._unit

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._attribute)
        if self._attribute == "vehicleState":
            return self._map_vehicle_state(value)
        return value

    # Keep legacy `state` property for compatibility
    @property
    def state(self):
        return self.native_value

    @property
    def icon(self):
        if self._attribute == "vehicleState":
            return self._get_vehicle_state_icon()
        return self._icon

    def _map_vehicle_state(self, value):
        mapper = {1: "Ready", 2: "Connected", 3: "Charging", 5: "Error"}
        return mapper.get(value, "Unknown")

    def _get_vehicle_state_icon(self):
        state = self._map_vehicle_state(
            self.coordinator.data.get("vehicleState") if self.coordinator.data else None
        )
        return {
            "Ready": "mdi:ev-station",
            "Connected": "mdi:car-connected",
            "Charging": "mdi:car-electric",
            "Error": "mdi:alert-circle",
        }.get(state, "mdi:help-circle")


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the SmartWB sensors."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = entry_data["coordinator"]
    device_name = config_entry.data["name"]
    unique_id = config_entry.unique_id

    sensors = [
        SmartWBSensor(coordinator, "actualCurrent",   "A",       "Actual Current",         unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "actualPower",     "kW",      "Actual Power",           unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(coordinator, "duration",        "Minutes", "Duration",               unique_id, device_name, "mdi:clock-time-eight-outline"),
        SmartWBSensor(coordinator, "vehicleState",    None,      "Vehicle State",          unique_id, device_name),
        SmartWBSensor(coordinator, "maxCurrent",      "A",       "Max Current",            unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "actualCurrentMA", "mA",      "Actual Current (mA)",    unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "alwaysActive",    None,      "Always Active",          unique_id, device_name, "mdi:clock-time-eight-outline"),
        SmartWBSensor(coordinator, "lastActionUser",  None,      "Last Action User",       unique_id, device_name),
        SmartWBSensor(coordinator, "lastActionUID",   None,      "Last Action UID",        unique_id, device_name),
        SmartWBSensor(coordinator, "energy",          "kWh",     "Energy",                 unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(coordinator, "mileage",         "km",      "Mileage",                unique_id, device_name, "mdi:map-marker-distance"),
        SmartWBSensor(coordinator, "meterReading",    "kWh",     "Meter Reading",          unique_id, device_name, "mdi:meter-electric"),
        SmartWBSensor(coordinator, "currentP1",       "A",       "Current Phase 1",        unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "currentP2",       "A",       "Current Phase 2",        unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "currentP3",       "A",       "Current Phase 3",        unique_id, device_name, "mdi:current-ac"),
        SmartWBSensor(coordinator, "voltageP1",       "V",       "Voltage Phase 1",        unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(coordinator, "voltageP2",       "V",       "Voltage Phase 2",        unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(coordinator, "voltageP3",       "V",       "Voltage Phase 3",        unique_id, device_name, "mdi:lightning-bolt"),
        SmartWBSensor(coordinator, "useMeter",        None,      "Use Meter",              unique_id, device_name),
        SmartWBSensor(coordinator, "RFIDUID",         None,      "RFID UID",               unique_id, device_name),
    ]

    async_add_entities(sensors)
