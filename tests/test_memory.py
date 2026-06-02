"""Tests for Conversation Memory storage and recall."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.conversation_memory.const import CONF_MAX_TURNS, DOMAIN
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
    assert "thermostat" in memories[0].user_text


async def test_build_context_formats_recalled_memory(hass):
    """Test prompt-ready context is built from relevant memories."""
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

    assert "Relevant previous Home Assistant conversation memory" in context
    assert "garage door automation" in context
    assert "close at 9 PM" in context
