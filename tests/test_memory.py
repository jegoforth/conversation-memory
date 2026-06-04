"""Tests for Voice Assist Recall storage and recall."""

from datetime import UTC, datetime, timedelta

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.conversation_memory.const import (
    ATTR_CONTEXT,
    ATTR_RELEVANT,
    ATTR_SESSION_ID,
    ATTR_SUMMARY,
    ATTR_SUMMARY_COUNT,
    ATTR_TURN_COUNT,
    ATTR_TURN_ID,
    CONF_MAX_TURNS,
    CONF_RAW_TURN_RETENTION_DAYS,
    CONF_SESSION_SUMMARY_RETENTION_DAYS,
    DOMAIN,
)
from custom_components.conversation_memory.memory import ConversationMemoryStore


class FakeStore:
    """In-memory replacement for Home Assistant's storage helper."""

    def __init__(self) -> None:
        """Initialize fake storage."""
        self.data = None

    async def async_load(self):
        """Load stored data."""
        return self.data

    async def async_save(self, data):
        """Save data."""
        self.data = data


def _mock_entry() -> MockConfigEntry:
    """Create a mock config entry for memory tests."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MAX_TURNS: 500,
            CONF_RAW_TURN_RETENTION_DAYS: 90,
            CONF_SESSION_SUMMARY_RETENTION_DAYS: 365,
        },
    )


async def test_recall_can_filter_by_speaker(hass):
    """Test recalled memories can be scoped by speaker."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-1",
        user_text="Set the thermostat to 70 tomorrow morning",
        assistant_text="I will remember the thermostat plan.",
        speaker_id="speaker-john",
        person_id="person.john",
    )
    await store.async_add_turn(
        conversation_id="conversation-2",
        user_text="Remind me about the garden lights",
        assistant_text="I will remember the garden lights.",
        speaker_id="speaker-sarah",
        person_id="person.sarah",
    )

    memories = await store.async_recall(
        "thermostat",
        5,
        speaker_id="speaker-john",
    )

    assert len(memories) == 1
    assert memories[0].speaker_id == "speaker-john"
    assert memories[0].person_id == "person.john"
    assert memories[0].session_id == "conversation-1"
    assert memories[0].as_response_dict()[ATTR_TURN_ID]
    assert memories[0].as_response_dict()[ATTR_SESSION_ID] == "conversation-1"
    assert "thermostat" in memories[0].user_text


async def test_build_context_formats_recalled_memory(hass):
    """Test prompt-ready context is built from relevant turns."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-1",
        user_text="We discussed garage door automation",
        assistant_text="The garage door should close at 9 PM.",
        speaker_id="speaker-john",
    )

    context = await store.async_build_context(
        "garage door",
        5,
        speaker_id="speaker-john",
    )

    assert "Relevant previous Voice Assist Recall context" in context
    assert "garage door automation" in context
    assert "close at 9 PM" in context


async def test_recall_can_filter_by_session(hass):
    """Test recalled memories can be scoped by session."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-1",
        session_id="session-alpha",
        user_text="We discussed the Twilio assistant",
        assistant_text="The Twilio assistant needs PIN authentication.",
    )
    await store.async_add_turn(
        conversation_id="conversation-2",
        session_id="session-beta",
        user_text="We discussed kitchen lights",
        assistant_text="The kitchen lights should dim at night.",
    )

    memories = await store.async_recall(
        "assistant",
        5,
        session_id="session-alpha",
    )

    assert len(memories) == 1
    assert memories[0].session_id == "session-alpha"
    assert "Twilio" in memories[0].user_text


async def test_recall_accepts_conversation_id_filter(hass):
    """Test recalled memories can be scoped by conversation ID."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-alpha",
        session_id="session-alpha",
        user_text="We discussed recall filtering",
        assistant_text="Conversation filters should work.",
    )
    await store.async_add_turn(
        conversation_id="conversation-beta",
        session_id="session-beta",
        user_text="We discussed unrelated lights",
        assistant_text="Lighting filters should not match.",
    )

    memories = await store.async_recall(
        "filters",
        5,
        conversation_id="conversation-alpha",
    )

    assert len(memories) == 1
    assert memories[0].conversation_id == "conversation-alpha"


async def test_search_session_summaries(hass):
    """Test session summaries can be searched by topic."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_save_session_summary(
        session_id="session-alpha",
        title="Twilio assistant planning",
        summary="Discussed PIN authentication for the Twilio assistant.",
        topics=["twilio", "authentication"],
        importance=2,
        speaker_id="speaker-john",
    )
    await store.async_save_session_summary(
        session_id="session-beta",
        title="Lighting automation",
        summary="Discussed dimming kitchen lights at night.",
        topics=["lighting"],
        speaker_id="speaker-john",
    )

    summaries = await store.async_search_session_summaries(
        "Twilio authentication",
        5,
        speaker_id="speaker-john",
    )

    assert len(summaries) == 1
    assert summaries[0].session_id == "session-alpha"
    assert summaries[0].as_response_dict()[ATTR_SUMMARY].startswith("Discussed PIN")


async def test_build_context_prefers_session_summaries(hass):
    """Test prompt-ready context includes summaries before supporting turns."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-1",
        session_id="session-alpha",
        user_text="Should the recall project add summaries?",
        assistant_text="Yes, summaries should come before raw turns.",
    )
    await store.async_save_session_summary(
        session_id="session-alpha",
        title="Recall architecture",
        summary="Decided session summaries should be used before raw turns.",
        topics=["recall", "summaries"],
    )

    context = await store.async_build_context("recall summaries", 5)

    summary_index = context.index("Session summaries:")
    turns_index = context.index("Supporting turns:")
    assert summary_index < turns_index
    assert "Recall architecture" in context
    assert "Should the recall project add summaries?" in context


async def test_retention_prunes_old_turns_and_summaries(hass):
    """Test retention removes expired raw turns and session summaries."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    old_turn_date = datetime.now(UTC) - timedelta(days=91)
    old_summary_date = datetime.now(UTC) - timedelta(days=366)
    recent_date = datetime.now(UTC) - timedelta(days=1)
    fake_store.data = {
        "turns": [
            {
                "turn_id": "old-turn",
                "session_id": "old-session",
                "conversation_id": "old-conversation",
                "user_text": "Old raw turn",
                "assistant_text": "Old raw response",
                "created_at": old_turn_date.isoformat(),
            },
            {
                "turn_id": "recent-turn",
                "session_id": "recent-session",
                "conversation_id": "recent-conversation",
                "user_text": "Recent raw turn",
                "assistant_text": "Recent raw response",
                "created_at": recent_date.isoformat(),
            },
        ],
        "session_summaries": [
            {
                "session_id": "old-session",
                "started_at": old_summary_date.isoformat(),
                "ended_at": old_summary_date.isoformat(),
                "title": "Old summary",
                "summary": "Old session summary",
                "topics": [],
                "importance": 0,
                "related_turn_ids": [],
            },
            {
                "session_id": "recent-session",
                "started_at": recent_date.isoformat(),
                "ended_at": recent_date.isoformat(),
                "title": "Recent summary",
                "summary": "Recent session summary",
                "topics": [],
                "importance": 0,
                "related_turn_ids": [],
            },
        ],
    }
    store._store = fake_store

    await store.async_load()

    memories = await store.async_recall("raw", 5)
    summaries = await store.async_search_session_summaries("summary", 5)

    assert [memory.turn_id for memory in memories] == ["recent-turn"]
    assert [summary.session_id for summary in summaries] == ["recent-session"]
    assert fake_store.data["turns"][0]["turn_id"] == "recent-turn"
    assert fake_store.data["session_summaries"][0]["session_id"] == "recent-session"


async def test_prepare_recall_context_returns_relevant_summary(hass):
    """Test prepared recall context exposes concise relevant summary metadata."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_save_session_summary(
        session_id="session-alpha",
        title="Voice Assist Recall testing",
        summary="Confirmed the private recall phrase was blue circuit.",
        topics=["voice assist recall", "testing"],
        importance=2,
    )

    prepared_context = await store.async_prepare_recall_context(
        "What was the private recall phrase?",
        5,
    )

    assert prepared_context[ATTR_RELEVANT] is True
    assert prepared_context[ATTR_SUMMARY_COUNT] == 1
    assert prepared_context[ATTR_TURN_COUNT] == 0
    assert "Voice Assist Recall testing" in prepared_context[ATTR_CONTEXT]
    assert "blue circuit" in prepared_context[ATTR_CONTEXT]


async def test_prepare_recall_context_returns_not_relevant_for_unrelated_query(hass):
    """Test prepared recall context reports no relevance when nothing matches."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_save_session_summary(
        session_id="session-alpha",
        title="Lighting automation",
        summary="Discussed kitchen dimming at night.",
        topics=["lighting"],
    )

    prepared_context = await store.async_prepare_recall_context(
        "What was the private recall phrase?",
        5,
    )

    assert prepared_context[ATTR_RELEVANT] is False
    assert prepared_context[ATTR_CONTEXT] == ""
    assert prepared_context[ATTR_SUMMARY_COUNT] == 0
    assert prepared_context[ATTR_TURN_COUNT] == 0


async def test_prepare_recall_context_falls_back_to_turns_when_no_summary(hass):
    """Test prepared recall context can use raw turns when no summary exists."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-alpha",
        user_text="The project codename is copper bridge.",
        assistant_text="I will remember copper bridge for recall testing.",
    )

    prepared_context = await store.async_prepare_recall_context(
        "What is the project codename?",
        5,
    )

    assert prepared_context[ATTR_RELEVANT] is True
    assert prepared_context[ATTR_SUMMARY_COUNT] == 0
    assert prepared_context[ATTR_TURN_COUNT] == 1
    assert "copper bridge" in prepared_context[ATTR_CONTEXT]


async def test_prepare_recall_context_can_include_supporting_turns(hass):
    """Test prepared recall context can include raw turns when explicitly requested."""
    store = ConversationMemoryStore(hass, _mock_entry())
    fake_store = FakeStore()
    store._store = fake_store

    await store.async_add_turn(
        conversation_id="conversation-alpha",
        session_id="session-alpha",
        user_text="We decided session summaries should lead recall.",
        assistant_text="Supporting turns should stay optional.",
    )
    await store.async_save_session_summary(
        session_id="session-alpha",
        title="Recall prompt design",
        summary="Session summaries should lead prompt recall context.",
        topics=["recall", "prompt"],
    )

    prepared_context = await store.async_prepare_recall_context(
        "recall summaries prompt",
        5,
        include_turns=True,
    )

    assert prepared_context[ATTR_SUMMARY_COUNT] == 1
    assert prepared_context[ATTR_TURN_COUNT] == 1
    assert "Recall prompt design" in prepared_context[ATTR_CONTEXT]
    assert "Supporting turns should stay optional" in prepared_context[ATTR_CONTEXT]
