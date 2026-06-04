"""Tests for the Voice Assist Recall conversation adapter helpers."""

from custom_components.conversation_memory.const import (
    ATTR_CONTEXT,
    ATTR_RELEVANT,
)
from custom_components.conversation_memory.conversation import _build_extra_system_prompt


def test_build_extra_system_prompt_skips_irrelevant_context():
    """Test irrelevant recall does not change the downstream prompt."""
    prompt = _build_extra_system_prompt(
        "Existing prompt.",
        {
            ATTR_RELEVANT: False,
            ATTR_CONTEXT: "",
        },
    )

    assert prompt == "Existing prompt."


def test_build_extra_system_prompt_appends_relevant_context():
    """Test relevant recall is appended to the downstream prompt."""
    prompt = _build_extra_system_prompt(
        "Existing prompt.",
        {
            ATTR_RELEVANT: True,
            ATTR_CONTEXT: "Relevant previous conversation recall:\n- Test memory.",
        },
    )

    assert prompt is not None
    assert prompt.startswith("Existing prompt.")
    assert "Use the following prior conversation recall" in prompt
    assert "Test memory" in prompt
