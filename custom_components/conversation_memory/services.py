"""Service handlers for Voice Assist Recall."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_AGENT_ID,
    ATTR_ASSISTANT_TEXT,
    ATTR_CONTEXT,
    ATTR_CONVERSATION_ID,
    ATTR_DEVICE_ID,
    ATTR_ENDED_AT,
    ATTR_IMPORTANCE,
    ATTR_LIMIT,
    ATTR_MEMORIES,
    ATTR_PERSON_ID,
    ATTR_QUERY,
    ATTR_RELATED_TURN_IDS,
    ATTR_ROOM_ID,
    ATTR_SESSION_ID,
    ATTR_SESSION_SUMMARIES,
    ATTR_SPEAKER_ID,
    ATTR_STARTED_AT,
    ATTR_SUMMARY,
    ATTR_TITLE,
    ATTR_TOPICS,
    ATTR_USER_TEXT,
    DEFAULT_RECALL_TURNS,
    DOMAIN,
    SERVICE_BUILD_CONTEXT,
    SERVICE_RECALL,
    SERVICE_SAVE_SESSION_SUMMARY,
    SERVICE_SAVE_TURN,
    SERVICE_SEARCH_SESSIONS,
)
from .memory import ConversationMemoryStore

OPTIONAL_SCOPE_SCHEMA = {
    vol.Optional(ATTR_SPEAKER_ID): cv.string,
    vol.Optional(ATTR_PERSON_ID): cv.string,
    vol.Optional(ATTR_CONVERSATION_ID): cv.string,
    vol.Optional(ATTR_SESSION_ID): cv.string,
}

SAVE_TURN_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_CONVERSATION_ID): cv.string,
        vol.Required(ATTR_USER_TEXT): cv.string,
        vol.Required(ATTR_ASSISTANT_TEXT): cv.string,
        vol.Optional(ATTR_SESSION_ID): cv.string,
        vol.Optional(ATTR_SPEAKER_ID): cv.string,
        vol.Optional(ATTR_PERSON_ID): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_ROOM_ID): cv.string,
        vol.Optional(ATTR_AGENT_ID): cv.string,
    }
)

RECALL_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_QUERY): cv.string,
        vol.Optional(ATTR_LIMIT, default=DEFAULT_RECALL_TURNS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)
        ),
        **OPTIONAL_SCOPE_SCHEMA,
    }
)

BUILD_CONTEXT_SCHEMA = RECALL_SCHEMA

SESSION_SCOPE_SCHEMA = {
    vol.Optional(ATTR_SPEAKER_ID): cv.string,
    vol.Optional(ATTR_PERSON_ID): cv.string,
    vol.Optional(ATTR_SESSION_ID): cv.string,
}

SAVE_SESSION_SUMMARY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SESSION_ID): cv.string,
        vol.Required(ATTR_SUMMARY): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
        vol.Optional(ATTR_STARTED_AT): cv.string,
        vol.Optional(ATTR_ENDED_AT): cv.string,
        vol.Optional(ATTR_TOPICS, default=[]): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_IMPORTANCE, default=0): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=10)
        ),
        vol.Optional(ATTR_RELATED_TURN_IDS, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(ATTR_SPEAKER_ID): cv.string,
        vol.Optional(ATTR_PERSON_ID): cv.string,
        vol.Optional(ATTR_DEVICE_ID): cv.string,
        vol.Optional(ATTR_ROOM_ID): cv.string,
        vol.Optional(ATTR_AGENT_ID): cv.string,
    }
)

SEARCH_SESSIONS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_QUERY): cv.string,
        vol.Optional(ATTR_LIMIT, default=DEFAULT_RECALL_TURNS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)
        ),
        **SESSION_SCOPE_SCHEMA,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register Voice Assist Recall services."""

    async def async_save_turn(call: ServiceCall) -> dict[str, Any]:
        store = _get_store(hass)
        await store.async_add_turn(
            conversation_id=call.data[ATTR_CONVERSATION_ID],
            user_text=call.data[ATTR_USER_TEXT],
            assistant_text=call.data[ATTR_ASSISTANT_TEXT],
            session_id=call.data.get(ATTR_SESSION_ID),
            speaker_id=call.data.get(ATTR_SPEAKER_ID),
            person_id=call.data.get(ATTR_PERSON_ID),
            device_id=call.data.get(ATTR_DEVICE_ID),
            room_id=call.data.get(ATTR_ROOM_ID),
            agent_id=call.data.get(ATTR_AGENT_ID),
        )
        return {"saved": True, "memory_count": store.memory_count}

    async def async_recall(call: ServiceCall) -> dict[str, Any]:
        store = _get_store(hass)
        memories = await store.async_recall(
            call.data[ATTR_QUERY],
            call.data[ATTR_LIMIT],
            speaker_id=call.data.get(ATTR_SPEAKER_ID),
            person_id=call.data.get(ATTR_PERSON_ID),
            conversation_id=call.data.get(ATTR_CONVERSATION_ID),
            session_id=call.data.get(ATTR_SESSION_ID),
        )
        return {ATTR_MEMORIES: [memory.as_response_dict() for memory in memories]}

    async def async_build_context(call: ServiceCall) -> dict[str, Any]:
        store = _get_store(hass)
        context = await store.async_build_context(
            call.data[ATTR_QUERY],
            call.data[ATTR_LIMIT],
            speaker_id=call.data.get(ATTR_SPEAKER_ID),
            person_id=call.data.get(ATTR_PERSON_ID),
            conversation_id=call.data.get(ATTR_CONVERSATION_ID),
            session_id=call.data.get(ATTR_SESSION_ID),
        )
        return {ATTR_CONTEXT: context}

    async def async_save_session_summary(call: ServiceCall) -> dict[str, Any]:
        store = _get_store(hass)
        await store.async_save_session_summary(
            session_id=call.data[ATTR_SESSION_ID],
            summary=call.data[ATTR_SUMMARY],
            title=call.data.get(ATTR_TITLE),
            started_at=call.data.get(ATTR_STARTED_AT),
            ended_at=call.data.get(ATTR_ENDED_AT),
            topics=call.data[ATTR_TOPICS],
            importance=call.data[ATTR_IMPORTANCE],
            related_turn_ids=call.data[ATTR_RELATED_TURN_IDS],
            speaker_id=call.data.get(ATTR_SPEAKER_ID),
            person_id=call.data.get(ATTR_PERSON_ID),
            device_id=call.data.get(ATTR_DEVICE_ID),
            room_id=call.data.get(ATTR_ROOM_ID),
            agent_id=call.data.get(ATTR_AGENT_ID),
        )
        return {"saved": True}

    async def async_search_sessions(call: ServiceCall) -> dict[str, Any]:
        store = _get_store(hass)
        summaries = await store.async_search_session_summaries(
            call.data[ATTR_QUERY],
            call.data[ATTR_LIMIT],
            speaker_id=call.data.get(ATTR_SPEAKER_ID),
            person_id=call.data.get(ATTR_PERSON_ID),
            session_id=call.data.get(ATTR_SESSION_ID),
        )
        return {
            ATTR_SESSION_SUMMARIES: [
                summary.as_response_dict() for summary in summaries
            ]
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_TURN,
        async_save_turn,
        schema=SAVE_TURN_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RECALL,
        async_recall,
        schema=RECALL_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_BUILD_CONTEXT,
        async_build_context,
        schema=BUILD_CONTEXT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAVE_SESSION_SUMMARY,
        async_save_session_summary,
        schema=SAVE_SESSION_SUMMARY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEARCH_SESSIONS,
        async_search_sessions,
        schema=SEARCH_SESSIONS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unregister Voice Assist Recall services."""
    hass.services.async_remove(DOMAIN, SERVICE_SAVE_TURN)
    hass.services.async_remove(DOMAIN, SERVICE_RECALL)
    hass.services.async_remove(DOMAIN, SERVICE_BUILD_CONTEXT)
    hass.services.async_remove(DOMAIN, SERVICE_SAVE_SESSION_SUMMARY)
    hass.services.async_remove(DOMAIN, SERVICE_SEARCH_SESSIONS)


def _get_store(hass: HomeAssistant) -> ConversationMemoryStore:
    """Return the active memory store."""
    stores = hass.data.get(DOMAIN, {})
    if not stores:
        raise RuntimeError("Voice Assist Recall is not configured")

    return next(iter(stores.values()))
