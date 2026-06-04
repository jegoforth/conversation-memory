"""Conversation adapter platform for Voice Assist Recall."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.intent import IntentResponse

from .const import (
    ATTR_CONTEXT,
    ATTR_RELEVANT,
    CONF_ADAPTER_CONTEXT_MAX_LENGTH,
    CONF_ADAPTER_INCLUDE_TURNS,
    CONF_NAME,
    CONF_RECALL_TURNS,
    CONF_TARGET_AGENT_ID,
    DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH,
    DEFAULT_ADAPTER_INCLUDE_TURNS,
    DEFAULT_NAME,
    DEFAULT_RECALL_TURNS,
    DOMAIN,
)
from .memory import ConversationMemoryStore


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Voice Assist Recall conversation adapter entities."""
    store: ConversationMemoryStore = hass.data[DOMAIN][entry.entry_id]
    await store.async_load()
    async_add_entities([ConversationMemoryAdapter(entry, store)])


class ConversationMemoryAdapter(conversation.ConversationEntity):
    """Conversation adapter that injects relevant recall into another agent."""

    _attr_supported_features = conversation.ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry, store: ConversationMemoryStore) -> None:
        """Initialize the conversation adapter."""
        self._entry = entry
        self._store = store
        self._attr_name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_unique_id = f"{entry.entry_id}_adapter"

    @property
    def supported_languages(self) -> list[str] | str:
        """Return supported languages."""
        return MATCH_ALL

    async def async_prepare(self, language: str | None = None) -> None:
        """Prepare the adapter for a request."""
        await self._store.async_load()

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Prepare recall context and forward the request to the target agent."""
        conversation_id = user_input.conversation_id or uuid4().hex
        settings = self._settings
        target_agent_id = settings.get(CONF_TARGET_AGENT_ID, "").strip()

        prepared_context = await self._store.async_prepare_recall_context(
            user_input.text,
            settings.get(CONF_RECALL_TURNS, DEFAULT_RECALL_TURNS),
            include_turns=settings.get(
                CONF_ADAPTER_INCLUDE_TURNS,
                DEFAULT_ADAPTER_INCLUDE_TURNS,
            ),
            max_length=settings.get(
                CONF_ADAPTER_CONTEXT_MAX_LENGTH,
                DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH,
            ),
        )

        if not target_agent_id:
            speech = (
                "Voice Assist Recall is installed, but no downstream Assist "
                "agent is configured yet."
            )
            await self._save_turn(conversation_id, user_input, speech, None)
            return _result(conversation_id, user_input.language, speech)

        if target_agent_id in {user_input.agent_id, self.entity_id}:
            speech = (
                "Voice Assist Recall cannot forward to itself. Configure a "
                "different downstream Assist agent."
            )
            await self._save_turn(conversation_id, user_input, speech, target_agent_id)
            return _result(conversation_id, user_input.language, speech)

        extra_system_prompt = _build_extra_system_prompt(
            user_input.extra_system_prompt,
            prepared_context,
        )
        result = await conversation.async_converse(
            hass=self.hass,
            text=user_input.text,
            conversation_id=conversation_id,
            context=user_input.context,
            language=user_input.language,
            agent_id=target_agent_id,
            device_id=user_input.device_id,
            satellite_id=user_input.satellite_id,
            extra_system_prompt=extra_system_prompt,
        )

        assistant_text = _extract_plain_speech(result)
        if assistant_text:
            await self._save_turn(
                result.conversation_id or conversation_id,
                user_input,
                assistant_text,
                target_agent_id,
            )

        return result

    @property
    def _settings(self) -> dict[str, Any]:
        """Return merged setup data and runtime options."""
        return {**self._entry.data, **self._entry.options}

    async def _save_turn(
        self,
        conversation_id: str,
        user_input: conversation.ConversationInput,
        assistant_text: str,
        agent_id: str | None,
    ) -> None:
        """Persist the completed adapter turn."""
        await self._store.async_add_turn(
            conversation_id=conversation_id,
            user_text=user_input.text,
            assistant_text=assistant_text,
            agent_id=agent_id,
            device_id=user_input.device_id,
        )


def _build_extra_system_prompt(
    existing_prompt: str | None,
    prepared_context: dict[str, Any],
) -> str | None:
    """Append relevant recall context to the downstream agent prompt."""
    if not prepared_context.get(ATTR_RELEVANT):
        return existing_prompt

    recall_context = prepared_context.get(ATTR_CONTEXT)
    if not recall_context:
        return existing_prompt

    recall_prompt = (
        "Use the following prior conversation recall only if it is relevant to "
        "the user's current request. Do not mention this recall block unless it "
        "helps answer the user.\n\n"
        f"{recall_context}"
    )
    if existing_prompt:
        return f"{existing_prompt}\n\n{recall_prompt}"
    return recall_prompt


def _extract_plain_speech(result: conversation.ConversationResult) -> str:
    """Extract plain speech from a conversation result."""
    plain_speech = result.response.speech.get("plain")
    if plain_speech:
        speech = plain_speech.get("speech")
        if isinstance(speech, str):
            return speech
    return ""


def _result(
    conversation_id: str,
    language: str,
    speech: str,
) -> conversation.ConversationResult:
    """Create a simple conversation result."""
    response = IntentResponse(language=language)
    response.async_set_speech(speech)
    return conversation.ConversationResult(
        conversation_id=conversation_id,
        response=response,
        continue_conversation=True,
    )
