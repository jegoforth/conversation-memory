"""Conversation Memory for Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .memory import ConversationMemoryStore
from .services import async_setup_services, async_unload_services

PLATFORMS: list[Platform] = [Platform.CONVERSATION, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Conversation Memory from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    if not hass.data[DOMAIN]:
        await async_setup_services(hass)

    hass.data[DOMAIN][entry.entry_id] = ConversationMemoryStore(hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            async_unload_services(hass)

    return unload_ok
