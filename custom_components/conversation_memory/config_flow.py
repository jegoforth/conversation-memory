"""Config flow for Voice Assist Recall."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ADAPTER_CONTEXT_MAX_LENGTH,
    CONF_ADAPTER_INCLUDE_TURNS,
    CONF_MAX_TURNS,
    CONF_NAME,
    CONF_RAW_TURN_RETENTION_DAYS,
    CONF_RECALL_TURNS,
    CONF_SESSION_SUMMARY_RETENTION_DAYS,
    CONF_TARGET_AGENT_ID,
    DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH,
    DEFAULT_ADAPTER_INCLUDE_TURNS,
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
        vol.Optional(CONF_TARGET_AGENT_ID, default=""): str,
        vol.Required(
            CONF_ADAPTER_INCLUDE_TURNS,
            default=DEFAULT_ADAPTER_INCLUDE_TURNS,
        ): bool,
        vol.Required(
            CONF_ADAPTER_CONTEXT_MAX_LENGTH,
            default=DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH,
        ): vol.All(vol.Coerce(int), vol.Range(min=200, max=4000)),
    }
)


class ConversationMemoryConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voice Assist Recall."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ConversationMemoryOptionsFlow:
        """Create the options flow."""
        return ConversationMemoryOptionsFlow(config_entry)

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


class ConversationMemoryOptionsFlow(config_entries.OptionsFlow):
    """Handle Voice Assist Recall options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self._config_entry.data, **self._config_entry.options}
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_TARGET_AGENT_ID,
                    default=current.get(CONF_TARGET_AGENT_ID, ""),
                ): str,
                vol.Required(
                    CONF_ADAPTER_INCLUDE_TURNS,
                    default=current.get(
                        CONF_ADAPTER_INCLUDE_TURNS,
                        DEFAULT_ADAPTER_INCLUDE_TURNS,
                    ),
                ): bool,
                vol.Required(
                    CONF_ADAPTER_CONTEXT_MAX_LENGTH,
                    default=current.get(
                        CONF_ADAPTER_CONTEXT_MAX_LENGTH,
                        DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH,
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=200, max=4000)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
