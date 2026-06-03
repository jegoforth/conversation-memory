"""Tests for Voice Assist Recall storage and recall."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.conversation_memory.const import (
    CONF_MAX_TURNS,
    ATTR_SESSION_ID,
    ATTR_SUMMARY,
    ATTR_TURN_ID,
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
    return MockConfigEntry(domain=DOMAIN, data={CONF_MAX_TURNS: 500})


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
