"""Persistent memory helpers for Conversation Memory."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.storage import Store

from .const import CONF_MAX_TURNS, DEFAULT_MAX_TURNS, STORAGE_KEY, STORAGE_VERSION

WORD_RE = re.compile(r"[a-z0-9_']+", re.IGNORECASE)
STOP_WORDS = {
    "a",
    "about",
    "and",
    "are",
    "did",
    "do",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "was",
    "we",
    "what",
    "with",
    "you",
}


@dataclass(slots=True)
class MemoryTurn:
    """A remembered user/assistant exchange."""

    conversation_id: str
    user_text: str
    assistant_text: str
    created_at: str
    speaker_id: str | None = None
    person_id: str | None = None
    device_id: str | None = None
    room_id: str | None = None
    agent_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryTurn:
        """Create a memory turn from stored data."""
        return cls(
            conversation_id=str(data["conversation_id"]),
            user_text=str(data["user_text"]),
            assistant_text=str(data["assistant_text"]),
            created_at=str(data["created_at"]),
            speaker_id=data.get("speaker_id"),
            person_id=data.get("person_id"),
            device_id=data.get("device_id"),
            room_id=data.get("room_id"),
            agent_id=data.get("agent_id"),
        )

    def as_response_dict(self) -> dict[str, Any]:
        """Return a service-response-safe dictionary."""
        return asdict(self)


class ConversationMemoryStore:
    """Store and recall prior conversation turns."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the store."""
        self._entry = entry
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry.entry_id}"
        )
        self._loaded = False
        self._turns: list[MemoryTurn] = []
        self._listeners: list[CALLBACK_TYPE] = []

    @property
    def memory_count(self) -> int:
        """Return the number of remembered turns."""
        return len(self._turns)

    async def async_load(self) -> None:
        """Load memories from Home Assistant storage."""
        if self._loaded:
            return

        data = await self._store.async_load()
        turns = data.get("turns", []) if data else []
        self._turns = [MemoryTurn.from_dict(turn) for turn in turns]
        self._loaded = True

    async def async_add_turn(
        self,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        device_id: str | None = None,
        room_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Persist a user/assistant exchange."""
        await self.async_load()

        self._turns.append(
            MemoryTurn(
                conversation_id=conversation_id,
                user_text=user_text,
                assistant_text=assistant_text,
                created_at=datetime.now(UTC).isoformat(),
                speaker_id=speaker_id,
                person_id=person_id,
                device_id=device_id,
                room_id=room_id,
                agent_id=agent_id,
            )
        )

        max_turns = self._entry.data.get(CONF_MAX_TURNS, DEFAULT_MAX_TURNS)
        self._turns = self._turns[-max_turns:]
        await self._async_save()

    async def async_recall(
        self,
        query: str,
        limit: int,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        conversation_id: str | None = None,
    ) -> list[MemoryTurn]:
        """Recall relevant memories for a query."""
        await self.async_load()

        candidate_turns = [
            turn
            for turn in self._turns
            if _matches_scope(
                turn,
                speaker_id=speaker_id,
                person_id=person_id,
                conversation_id=conversation_id,
            )
        ]

        query_terms = _terms(query)
        if not query_terms:
            return list(reversed(candidate_turns[-limit:]))

        scored_turns: list[tuple[int, MemoryTurn]] = []
        for turn in candidate_turns:
            text_terms = _terms(f"{turn.user_text} {turn.assistant_text}")
            score = len(query_terms & text_terms)
            if score:
                scored_turns.append((score, turn))

        scored_turns.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
        return [turn for _, turn in scored_turns[:limit]]

    async def async_build_context(
        self,
        query: str,
        limit: int,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        conversation_id: str | None = None,
    ) -> str:
        """Build prompt-ready memory context for an AI provider."""
        memories = await self.async_recall(
            query,
            limit,
            speaker_id=speaker_id,
            person_id=person_id,
            conversation_id=conversation_id,
        )
        if not memories:
            return ""

        lines = ["Relevant previous Home Assistant conversation memory:"]
        for memory in memories:
            lines.append(f"- User: {memory.user_text}")
            lines.append(f"  Assistant: {memory.assistant_text}")

        return "\n".join(lines)

    def async_add_listener(self, listener: CALLBACK_TYPE) -> CALLBACK_TYPE:
        """Listen for memory changes."""
        self._listeners.append(listener)

        def remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return remove_listener

    async def _async_save(self) -> None:
        """Save memories to Home Assistant storage."""
        await self._store.async_save({"turns": [asdict(turn) for turn in self._turns]})
        for listener in self._listeners:
            listener()


def _terms(text: str) -> set[str]:
    """Return normalized searchable terms."""
    return {
        word.lower()
        for word in WORD_RE.findall(text)
        if len(word) > 2 and word.lower() not in STOP_WORDS
    }


def _matches_scope(
    turn: MemoryTurn,
    *,
    speaker_id: str | None,
    person_id: str | None,
    conversation_id: str | None,
) -> bool:
    """Return true if a memory turn matches optional recall scope."""
    if speaker_id is not None and turn.speaker_id != speaker_id:
        return False
    if person_id is not None and turn.person_id != person_id:
        return False
    return not (conversation_id is not None and turn.conversation_id != conversation_id)
