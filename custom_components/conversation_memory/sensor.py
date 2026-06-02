"""Sensor platform for Voice Assist Recall."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN
from .memory import ConversationMemoryStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Voice Assist Recall sensors from a config entry."""
    store: ConversationMemoryStore = hass.data[DOMAIN][entry.entry_id]
    await store.async_load()
    async_add_entities([ConversationMemoryCountSensor(entry, store)])


class ConversationMemoryCountSensor(SensorEntity):
    """Report the number of remembered conversation turns."""

    _attr_icon = "mdi:chat-processing-outline"

    def __init__(self, entry: ConfigEntry, store: ConversationMemoryStore) -> None:
        """Initialize the sensor."""
        self._entry = entry
        self._store = store
        name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_name = f"{name} Memories"
        self._attr_unique_id = f"{entry.entry_id}_memory_count"

    async def async_added_to_hass(self) -> None:
        """Register updates when memories change."""
        self.async_on_remove(self._store.async_add_listener(self._memory_updated))

    @property
    def native_value(self) -> int:
        """Return the sensor state."""
        return self._store.memory_count

    @callback
    def _memory_updated(self) -> None:
        """Write updated memory count to Home Assistant."""
        self.async_write_ha_state()
