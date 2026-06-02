# Conversation Memory for Home Assistant

Conversation Memory is a Home Assistant custom integration prototype for giving
Assist a persistent local memory across conversation windows.

## Problem

Home Assistant Assist tracks a conversation while the caller keeps passing the
same `conversation_id`, but that context is short-lived from the user's point of
view. If a voice session or browser window closes, the next interaction starts
fresh and the AI cannot refer back to older conversations.

## Goal

Create a local memory layer that can:

- save user/assistant turns beyond a single active conversation,
- recall relevant previous turns by topic,
- attach identity metadata from separate speaker recognition projects,
- provide services that any Assist agent, automation, or adapter can call,
- expose an optional conversation agent that can answer explicit recall requests.

## Architecture

The project is service-first. The reusable memory backend is independent from
the included demo conversation agent.

Speaker recognition, Assist adapters, and future LLM wrappers should call these
services instead of depending on the `Conversation Memory` conversation agent:

- `conversation_memory.save_turn`
- `conversation_memory.recall`
- `conversation_memory.build_context`

Each saved turn can include identity and source metadata:

```yaml
conversation_id: assist-session-id
speaker_id: speaker-john
person_id: person.john
device_id: voice_satellite_kitchen
room_id: kitchen
agent_id: conversation.openai
user_text: Continue what we discussed yesterday
assistant_text: We were talking about thermostat schedules.
```

This allows speaker recognition to remain a separate project while still giving
memory recall enough context to answer person-specific or device-specific
questions.

## Structure

```text
custom_components/
  conversation_memory/
    __init__.py
    conversation.py
    config_flow.py
    const.py
    manifest.json
    memory.py
    services.py
    services.yaml
    sensor.py
    translations/
      en.json
tests/
  test_config_flow.py
  test_memory.py
```

## Installation

### HACS

Conversation Memory can be installed as a HACS custom repository.

[Open HACS Repository on My](https://my.home-assistant.io/redirect/hacs_repository/?owner=jegoforth&repository=conversation-memory&category=integration)

Manual HACS install:

1. Open Home Assistant.
2. Go to `HACS`.
3. Open the menu and choose `Custom repositories`.
4. Add this repository URL:

```text
https://github.com/jegoforth/conversation-memory
```

5. Select category `Integration`.
6. Download the repository in HACS.
7. Restart Home Assistant.
8. Add the integration from:

```text
Settings > Devices & services > Add integration > Conversation Memory
```

### Manual

Copy or symlink `custom_components/conversation_memory` into your Home Assistant
configuration directory:

```text
<home-assistant-config>/custom_components/conversation_memory
```

Restart Home Assistant, then add the integration from:

```text
Settings > Devices & services > Add integration > Conversation Memory
```

## Current behavior

The implementation is intentionally local and provider-neutral:

- Any integration can save turns through `conversation_memory.save_turn`.
- Any integration can recall turns through `conversation_memory.recall`.
- LLM adapters can request prompt-ready memory through
  `conversation_memory.build_context`.
- Turns can be filtered by `speaker_id`, `person_id`, or `conversation_id`.
- Every turn handled by the optional `Conversation Memory` conversation agent is
  saved to Home Assistant storage.
- Recall requests such as "what did we talk about..." or "recall..." search old
  turns by shared topic words.
- The integration adds a sensor showing the number of remembered turns.

This does not yet wrap an external LLM provider. The next step is an adapter
that calls `conversation_memory.build_context`, prepends the result to the AI
prompt, then forwards the user request to the selected AI conversation agent.

## Development

Install development dependencies:

```powershell
python -m pip install -e ".[dev]"
```

Run checks:

```powershell
pytest
ruff check .
```

## Changelog

### 0.1.0

- Initial Conversation Memory custom integration.
- Added local persistent conversation memory storage.
- Added services for `save_turn`, `recall`, and `build_context`.
- Added optional Assist conversation agent for recall testing.
- Added memory count sensor.
- Added speaker/person/conversation metadata fields for future speaker
  recognition integration.
