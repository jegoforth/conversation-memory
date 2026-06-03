"""Persistent memory helpers for Voice Assist Recall."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re
from typing import Any
from uuid import uuid4

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

    turn_id: str
    session_id: str
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
        conversation_id = str(data["conversation_id"])
        return cls(
            turn_id=str(data.get("turn_id") or uuid4().hex),
            session_id=str(data.get("session_id") or conversation_id),
            conversation_id=conversation_id,
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


@dataclass(slots=True)
class SessionSummary:
    """A compact summary of a conversation session."""

    session_id: str
    started_at: str
    ended_at: str
    title: str
    summary: str
    topics: list[str]
    importance: int
    related_turn_ids: list[str]
    speaker_id: str | None = None
    person_id: str | None = None
    device_id: str | None = None
    room_id: str | None = None
    agent_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionSummary:
        """Create a session summary from stored data."""
        return cls(
            session_id=str(data["session_id"]),
            started_at=str(data["started_at"]),
            ended_at=str(data["ended_at"]),
            title=str(data.get("title") or "Untitled session"),
            summary=str(data["summary"]),
            topics=[str(topic) for topic in data.get("topics", [])],
            importance=int(data.get("importance", 0)),
            related_turn_ids=[
                str(turn_id) for turn_id in data.get("related_turn_ids", [])
            ],
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
        self._session_summaries: list[SessionSummary] = []
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
        summaries = data.get("session_summaries", []) if data else []
        self._turns = [MemoryTurn.from_dict(turn) for turn in turns]
        self._session_summaries = [
            SessionSummary.from_dict(summary) for summary in summaries
        ]
        self._loaded = True

    async def async_add_turn(
        self,
        conversation_id: str,
        user_text: str,
        assistant_text: str,
        *,
        session_id: str | None = None,
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
                turn_id=uuid4().hex,
                session_id=session_id or conversation_id,
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

    async def async_save_session_summary(
        self,
        session_id: str,
        summary: str,
        *,
        title: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
        topics: list[str] | None = None,
        importance: int = 0,
        related_turn_ids: list[str] | None = None,
        speaker_id: str | None = None,
        person_id: str | None = None,
        device_id: str | None = None,
        room_id: str | None = None,
        agent_id: str | None = None,
    ) -> None:
        """Persist or replace a session summary."""
        await self.async_load()

        now = datetime.now(UTC).isoformat()
        new_summary = SessionSummary(
            session_id=session_id,
            started_at=started_at or now,
            ended_at=ended_at or now,
            title=title or "Untitled session",
            summary=summary,
            topics=topics or [],
            importance=importance,
            related_turn_ids=related_turn_ids or [],
            speaker_id=speaker_id,
            person_id=person_id,
            device_id=device_id,
            room_id=room_id,
            agent_id=agent_id,
        )

        self._session_summaries = [
            existing
            for existing in self._session_summaries
            if existing.session_id != session_id
        ]
        self._session_summaries.append(new_summary)
        await self._async_save()

    async def async_recall(
        self,
        query: str,
        limit: int,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        session_id: str | None = None,
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
                session_id=session_id,
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

    async def async_search_session_summaries(
        self,
        query: str,
        limit: int,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        session_id: str | None = None,
    ) -> list[SessionSummary]:
        """Search relevant session summaries for a query."""
        await self.async_load()

        candidate_summaries = [
            summary
            for summary in self._session_summaries
            if _matches_summary_scope(
                summary,
                speaker_id=speaker_id,
                person_id=person_id,
                session_id=session_id,
            )
        ]

        query_terms = _terms(query)
        if not query_terms:
            candidate_summaries.sort(key=lambda summary: summary.ended_at, reverse=True)
            return candidate_summaries[:limit]

        scored_summaries: list[tuple[int, SessionSummary]] = []
        for summary in candidate_summaries:
            text_terms = _terms(
                f"{summary.title} {summary.summary} {' '.join(summary.topics)}"
            )
            score = len(query_terms & text_terms)
            if score:
                scored_summaries.append((score + summary.importance, summary))

        scored_summaries.sort(
            key=lambda item: (item[0], item[1].ended_at), reverse=True
        )
        return [summary for _, summary in scored_summaries[:limit]]

    async def async_build_context(
        self,
        query: str,
        limit: int,
        *,
        speaker_id: str | None = None,
        person_id: str | None = None,
        conversation_id: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Build prompt-ready memory context for an AI provider."""
        summaries = await self.async_search_session_summaries(
            query,
            limit,
            speaker_id=speaker_id,
            person_id=person_id,
            session_id=session_id,
        )
        turn_limit = limit if not summaries else max(0, limit - len(summaries))
        memories = []
        if turn_limit:
            memories = await self.async_recall(
                query,
                turn_limit,
                speaker_id=speaker_id,
                person_id=person_id,
                conversation_id=conversation_id,
                session_id=session_id,
            )
        if not summaries and not memories:
            return ""

        lines = ["Relevant previous Voice Assist Recall context:"]
        if summaries:
            lines.append("")
            lines.append("Session summaries:")
            for summary in summaries:
                lines.append(f"- {summary.title}: {summary.summary}")
                if summary.topics:
                    lines.append(f"  Topics: {', '.join(summary.topics)}")

        if memories:
            lines.append("")
            lines.append("Supporting turns:")
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
        await self._store.async_save(
            {
                "turns": [asdict(turn) for turn in self._turns],
                "session_summaries": [
                    asdict(summary) for summary in self._session_summaries
                ],
            }
        )
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
    session_id: str | None,
) -> bool:
    """Return true if a memory turn matches optional recall scope."""
    if speaker_id is not None and turn.speaker_id != speaker_id:
        return False
    if person_id is not None and turn.person_id != person_id:
        return False
    if conversation_id is not None and turn.conversation_id != conversation_id:
        return False
    return not (session_id is not None and turn.session_id != session_id)


def _matches_summary_scope(
    summary: SessionSummary,
    *,
    speaker_id: str | None,
    person_id: str | None,
    session_id: str | None,
) -> bool:
    """Return true if a session summary matches optional recall scope."""
    if speaker_id is not None and summary.speaker_id != speaker_id:
        return False
    if person_id is not None and summary.person_id != person_id:
        return False
    return not (session_id is not None and summary.session_id != session_id)
