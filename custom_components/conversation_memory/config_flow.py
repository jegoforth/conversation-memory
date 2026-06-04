"""Config flow for Voice Assist Recall."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_MAX_TURNS,
    CONF_NAME,
    CONF_RAW_TURN_RETENTION_DAYS,
    CONF_RECALL_TURNS,
    CONF_SESSION_SUMMARY_RETENTION_DAYS,
    DEFAULT_MAX_TURNS,
    DEFAULT_NAME,
    DEFAULT_RAW_TURN_RETENTION_DAYS,
    DEFAULT_RECALL_TURNS,
    DEFAULT_SESSION_SUMMARY_RETENTION_DAYS,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_MAX_TURNS, default=DEFAULT_MAX_TURNS): vol.All(
            vol.Coerce(int), vol.Range(min=20, max=5000)
        ),
        vol.Required(CONF_RECALL_TURNS, default=DEFAULT_RECALL_TURNS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)
        ),
        vol.Required(
            CONF_RAW_TURN_RETENTION_DAYS,
            default=DEFAULT_RAW_TURN_RETENTION_DAYS,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3650)),
        vol.Required(
            CONF_SESSION_SUMMARY_RETENTION_DAYS,
            default=DEFAULT_SESSION_SUMMARY_RETENTION_DAYS,
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=3650)),
    }
)


class ConversationMemoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voice Assist Recall."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data=user_input,
        )
