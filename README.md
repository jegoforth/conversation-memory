# Voice Assist Recall for Home Assistant

Voice Assist Recall is a Home Assistant custom integration prototype for giving
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
- expose an Assist adapter that can forward enriched requests to a selected AI
  conversation agent.

## Architecture

The project is service-first. The reusable memory backend is independent from
the included Assist adapter.

Speaker recognition, Assist adapters, and future LLM wrappers should call these
services instead of depending on the `Voice Assist Recall` conversation agent:

- `conversation_memory.save_turn`
- `conversation_memory.recall`
- `conversation_memory.build_context`
- `conversation_memory.prepare_recall_context`
- `conversation_memory.save_session_summary`
- `conversation_memory.search_sessions`

Each saved turn can include identity and source metadata:

```yaml
conversation_id: assist-session-id
session_id: recall-session-id
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

## Requirements

- Home Assistant with Assist enabled.
- HACS, if installing through the recommended HACS custom repository path.
- A Home Assistant version that supports config entries, custom integrations,
  Assist conversation agents, and service response data.
- Optional: a speaker recognition integration that can provide `speaker_id` or
  `person_id` metadata.
- Optional: an LLM-backed Assist agent or adapter that can call
  `conversation_memory.build_context` before forwarding a prompt.
- Recommended for adapter testing: an existing AI conversation agent entity ID
  to use as the downstream target, such as an OpenAI Conversation or Ollama
  conversation entity.

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

Voice Assist Recall can be installed as a HACS custom repository.

[![Open HACS Repository on My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jegoforth&repository=conversation-memory&category=integration)

[Open HACS Repository on My Home Assistant](https://my.home-assistant.io/redirect/hacs_repository/?owner=jegoforth&repository=conversation-memory&category=integration)

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
Settings > Devices & services > Add integration > Voice Assist Recall
```

During setup or from the integration options, set `Downstream Assist agent ID`
to the conversation agent that should receive the enriched request. Leave it
blank only if you want to test that the adapter loads without forwarding.

### Manual

Copy or symlink `custom_components/conversation_memory` into your Home Assistant
configuration directory:

```text
<home-assistant-config>/custom_components/conversation_memory
```

Restart Home Assistant, then add the integration from:

```text
Settings > Devices & services > Add integration > Voice Assist Recall
```

## Current behavior

The implementation is intentionally local and provider-neutral:

- Any integration can save turns through `conversation_memory.save_turn`.
- Any integration can recall turns through `conversation_memory.recall`.
- Any integration can save compact summaries through
  `conversation_memory.save_session_summary`.
- Any integration can search summaries through `conversation_memory.search_sessions`.
- LLM adapters can request prompt-ready memory through
  `conversation_memory.build_context`.
- Assist adapters or scripts can request concise, relevance-tagged recall
  through `conversation_memory.prepare_recall_context`.
- Turns and summaries can be filtered by `speaker_id`, `person_id`,
  `conversation_id`, or `session_id`.
- Raw turns are retained for 90 days by default.
- Session summaries are retained for 365 days by default.
- Both retention windows are configurable during setup.
- `build_context` prefers matching session summaries before adding supporting
  raw turns.
- `prepare_recall_context` returns `relevant`, `context`, `summary_count`, and
  `turn_count` so an adapter can include recall only when prior context was
  found.
- `prepare_recall_context` prefers summaries and only includes raw turns as a
  fallback unless `include_turns` is explicitly enabled.
- The Assist adapter is enabled and can forward requests to the configured
  downstream conversation agent.
- The adapter passes relevant recall through Home Assistant's
  `extra_system_prompt` conversation field.
- Recall requests such as "what did we talk about..." or "recall..." search old
  turns by shared topic words.
- The integration adds a sensor showing the number of remembered turns.

The adapter does not replace the selected AI provider. It prepares recall
context for the current request, appends it to the downstream agent's extra
system prompt only when relevant, forwards the request, and saves the completed
turn.

## Development Approach

![Built with Codex](https://img.shields.io/badge/Built%20with-Codex-000000?style=for-the-badge&logo=openai&logoColor=white)

Voice Assist Recall is being developed with Codex as an implementation partner.
The project is intentionally evolving in small, reviewable versions:

- Start with a provider-neutral memory backend.
- Keep speaker recognition separate and integrate through metadata.
- Prefer Home Assistant services as the integration boundary.
- Treat the included conversation agent as a test/demo surface, not the core
  dependency.
- Add provider adapters later, once the memory API is stable enough to avoid
  coupling the project to one AI backend.

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

### 0.5.0

- Re-enabled the Home Assistant conversation platform as an Assist adapter.
- Added configurable downstream Assist agent forwarding.
- Added adapter options for supporting raw turns and context length.
- Injects relevant recall through `extra_system_prompt` before forwarding to the
  downstream agent.
- Saves completed adapter user/assistant turns.
- Added options-flow and adapter prompt helper tests.

### 0.4.0

- Added `conversation_memory.prepare_recall_context`.
- Added concise recall responses with `relevant`, `context`, `summary_count`,
  and `turn_count`.
- Made prepared recall summary-first, with raw turns used only as a fallback or
  when `include_turns` is explicitly enabled.
- Added prompt-safe context length limiting for prepared recall.
- Added tests for relevant summaries, unrelated queries, raw-turn fallback, and
  explicit supporting-turn inclusion.

### 0.3.0

- Added configurable retention for raw turns and session summaries.
- Set default raw turn retention to 90 days.
- Set default session summary retention to 365 days.
- Added pruning for expired raw turns and session summaries during store load
  and writes.
- Documented topic summaries as a future indefinite-retention tier.

### 0.2.2

- Fixed `recall` and `build_context` calls that pass `conversation_id` into raw
  turn recall.

### 0.2.1

- Disabled the optional demo conversation platform to prevent install failure
  while the service-first backend is tested.
- Core services remain available for install and service-call testing.

### 0.2.0

- Added session summary storage.
- Added services for `save_session_summary` and `search_sessions`.
- Updated `build_context` to prefer relevant session summaries before raw turns.
- Added summary search by title, summary text, and topics.
- Added session summary tests and bumped the integration version to `0.2.0`.

### 0.1.0

- Initial Voice Assist Recall custom integration.
- Added local persistent Assist recall storage.
- Added services for `save_turn`, `recall`, and `build_context`.
- Added optional Assist conversation agent for recall testing.
- Added memory count sensor.
- Added speaker/person/conversation metadata fields for future speaker
  recognition integration.
