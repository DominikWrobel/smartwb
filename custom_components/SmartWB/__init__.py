from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, PLATFORMS

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up EVSE integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = config_entry.data

    # Create a device entry
#    device_registry = dr.async_get(hass)
#    device_registry.async_get_or_create(
#        config_entry_id=config_entry.entry_id,
#        identifiers={(DOMAIN, config_entry.unique_id)},
#        name=config_entry.data['name'],
#        manufacturer="EVSE",
#        model="EVSE Controller"
#    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
