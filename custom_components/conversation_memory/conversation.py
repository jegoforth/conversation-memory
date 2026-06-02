"""Conversation platform for Conversation Memory."""

from __future__ import annotations

from uuid import uuid4

from homeassistant.components import conversation
from homeassistant.components.conversation import (
    AssistantContent,
    ChatLog,
    ConversationEntity,
    ConversationEntityFeature,
    ConversationInput,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.intent import IntentResponse

from .const import (
    CONF_NAME,
    CONF_RECALL_TURNS,
    DEFAULT_NAME,
    DEFAULT_RECALL_TURNS,
    DOMAIN,
)
from .memory import ConversationMemoryStore, MemoryTurn

RECALL_TRIGGERS = (
    "what did we discuss",
    "what did we talk about",
    "recall",
    "remember when",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Conversation Memory conversation entities."""
    store: ConversationMemoryStore = hass.data[DOMAIN][entry.entry_id]
    await store.async_load()
    async_add_entities([ConversationMemoryAgent(entry, store)])


class ConversationMemoryAgent(ConversationEntity):
    """Conversation agent that persists and recalls previous exchanges."""

    _attr_supported_features = ConversationEntityFeature.CONTROL

    def __init__(self, entry: ConfigEntry, store: ConversationMemoryStore) -> None:
        """Initialize the conversation agent."""
        self._entry = entry
        self._store = store
        self._attr_name = entry.data.get(CONF_NAME, DEFAULT_NAME)
        self._attr_unique_id = f"{entry.entry_id}_agent"

    @property
    def supported_languages(self) -> list[str] | str:
        """Return supported languages."""
        return "*"

    async def async_prepare(self, language: str | None = None) -> None:
        """Prepare the agent for a request."""
        await self._store.async_load()

    async def _async_handle_message(
        self,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> conversation.ConversationResult:
        """Handle an incoming conversation message."""
        conversation_id = user_input.conversation_id or uuid4().hex
        recall_limit = self._entry.data.get(CONF_RECALL_TURNS, DEFAULT_RECALL_TURNS)

        if _is_recall_request(user_input.text):
            memories = await self._store.async_recall(user_input.text, recall_limit)
            speech = _format_memories(memories)
        else:
            memories = await self._store.async_recall(user_input.text, recall_limit)
            speech = _format_context_response(memories)

        await self._store.async_add_turn(
            conversation_id=conversation_id,
            user_text=user_input.text,
            assistant_text=speech,
            agent_id=user_input.agent_id,
        )

        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(agent_id=user_input.agent_id, content=speech)
        )

        response = IntentResponse(language=user_input.language)
        response.async_set_speech(speech)

        return conversation.ConversationResult(
            conversation_id=conversation_id,
            response=response,
            continue_conversation=True,
        )


def _is_recall_request(text: str) -> bool:
    """Return true if the user explicitly asks for prior context."""
    lowered = text.lower()
    return any(trigger in lowered for trigger in RECALL_TRIGGERS)


def _format_context_response(memories: list[MemoryTurn]) -> str:
    """Format a response for normal conversation turns."""
    if not memories:
        return (
            "I do not have relevant prior conversation memory yet. "
            "I saved this turn so we can refer back to it later."
        )

    return (
        "I found related prior context and saved this new turn. "
        "Ask me to recall it when you want the details."
    )


def _format_memories(memories: list[MemoryTurn]) -> str:
    """Format recalled memories for speech."""
    if not memories:
        return "I do not have a matching previous conversation yet."

    lines = ["Here is what I found from previous conversations:"]
    for memory in memories:
        lines.append(f"You said: {memory.user_text}")
        lines.append(f"I replied: {memory.assistant_text}")

    return "\n".join(lines)
