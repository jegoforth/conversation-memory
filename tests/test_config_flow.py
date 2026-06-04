"""Tests for the Voice Assist Recall config flow."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.conversation_memory.const import (
    CONF_MAX_TURNS,
    CONF_NAME,
    CONF_RAW_TURN_RETENTION_DAYS,
    CONF_RECALL_TURNS,
    CONF_SESSION_SUMMARY_RETENTION_DAYS,
    DOMAIN,
)


async def test_user_flow(hass):
    """Test creating an entry from the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Voice Assist Recall",
            CONF_MAX_TURNS: 100,
            CONF_RECALL_TURNS: 5,
            CONF_RAW_TURN_RETENTION_DAYS: 90,
            CONF_SESSION_SUMMARY_RETENTION_DAYS: 365,
        },
    )

    assert result["type"] == "create_entry"
    assert result["title"] == "Voice Assist Recall"
    assert result["data"] == {
        CONF_NAME: "Voice Assist Recall",
        CONF_MAX_TURNS: 100,
        CONF_RECALL_TURNS: 5,
        CONF_RAW_TURN_RETENTION_DAYS: 90,
        CONF_SESSION_SUMMARY_RETENTION_DAYS: 365,
    }


async def test_duplicate_name_aborts(hass):
    """Test duplicate entries are rejected."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Voice Assist Recall",
        data={
            CONF_NAME: "Voice Assist Recall",
            CONF_MAX_TURNS: 100,
            CONF_RECALL_TURNS: 5,
            CONF_RAW_TURN_RETENTION_DAYS: 90,
            CONF_SESSION_SUMMARY_RETENTION_DAYS: 365,
        },
        unique_id=DOMAIN,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data={CONF_NAME: "Test Integration"},
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
