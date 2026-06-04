# Voice Assist Recall Architecture

This document is the shared architecture guide for this repository. It is intended to act as a communication bridge between Eric, ChatGPT, and Codex.

Eric uses ChatGPT primarily to align overall goals, project direction, naming, and architecture. Eric uses Codex primarily to implement, refactor, test, and debug the code. When either assistant needs project context, this file should be treated as the current source of truth unless Eric says otherwise.

## Project Name

The public/community-facing project name is **Voice Assist Recall**.

The repository currently uses the working name `conversation-memory` and the Home Assistant integration domain `conversation_memory`. Because the project is still early, a future rename to `voice-assist-recall` / `voice_assist_recall` should be considered before wider release.

## Overall Goal

Voice Assist Recall provides a local, provider-neutral conversation history and recall layer for Home Assistant Assist.

The goal is to let a voice assistant refer back to previous conversations after the active Home Assistant `conversation_id` or UI session is gone.

It should support workflows such as:

- “What were we talking about yesterday?”
- “Continue what we were working on earlier.”
- “What did Shelley say about that?”
- “What did we decide about the memory project?”
- “Use the context from my previous conversation about the Twilio assistant.”

The integration should remain useful beyond one household or one assistant persona. Eric’s private assistant is named Elspeth, but this project should stay generic and community-friendly.

## Cross-Project Architecture Contract

Voice Assist Recall is one layer in a larger Home Assistant voice AI architecture. It must stay independent while remaining easy to compose with the other layers.

The intended project boundaries are:

```text
House Memory
  Stable, curated household and profile context.

Voice Assist Recall
  Historical conversation turns, sessions, summaries, and recall search.

Identity Context
  Speaker/person/source identification supplied by Home Assistant, speaker
  recognition, Twilio PINs, companion apps, or other adapters.

Context Engine / Assist Adapter
  Runtime prompt assembly that decides what stable memory, recalled history,
  Home Assistant state, and request metadata belong in the current AI prompt.
```

Voice Assist Recall should not become the stable household profile store. It should store historical conversation data and retrieve relevant prior context.

House Memory should remain the reviewed and curated destination for durable facts. Voice Assist Recall may suggest durable facts discovered from conversations, but those facts should only become stable household/profile memory through an explicit promotion or write path.

Shared integration principles:

- Keep each project installable and useful on its own.
- Communicate through Home Assistant-native services, sensors, events, or clear adapter contracts instead of hard dependencies where practical.
- Do not assume one required LLM provider, conversation agent, speaker recognition integration, or assistant persona.
- Keep private household examples out of public defaults and diagnostics.
- Keep stable memory concise; keep historical recall searchable and timestamped.
- Prefer explicit, reviewable memory writes over automatic permanent memory.

When developing Voice Assist Recall, Codex and ChatGPT should protect this boundary: House Memory answers “what should the assistant know?” Voice Assist Recall answers “what did we talk about?” The Context Engine decides “what matters for this request?”

## Relationship to Other Projects

Voice Assist Recall is one part of a larger Home Assistant voice AI architecture.

### HA Voice Memory

HA Voice Memory is a separate project for stable, curated profile and household memory.

It stores durable facts such as:

- house profile
- user profiles
- assistant personality preferences
- shared household preferences
- long-lived device/room/project facts

HA Voice Memory should stay compact, curated, and relatively stable.

### Voice Assist Recall

Voice Assist Recall stores and retrieves conversation history.

It stores things such as:

- user/assistant turns
- conversation sessions
- session summaries
- topic summaries
- metadata about speaker, person, device, room, and agent
- candidate facts that may later be promoted into HA Voice Memory

Voice Assist Recall should be searchable, timestamped, and historical. It should not become a junk drawer of permanent profile facts.

### Identity Context

Identity Context is a separate concern. Voice Assist Recall should not perform speaker recognition itself.

Instead, integrations such as speaker recognition, the Home Assistant companion app, Twilio PIN authentication, or other adapters should pass identity metadata into Voice Assist Recall.

Useful identity/source metadata includes:

- `speaker_id`
- `person_id`
- `device_id`
- `room_id`
- `agent_id`
- `conversation_id`

### Context Engine

The long-term architecture should include a Context Engine or adapter that assembles the actual prompt context for the selected AI conversation agent.

The Context Engine should read from:

- HA Voice Memory for stable facts
- Voice Assist Recall for relevant past conversation context
- Home Assistant state when relevant
- current request metadata

Voice Assist Recall should provide services that make this possible, but it should not need to own the entire AI pipeline.

## Architectural Principle

Keep the layers separate, but make them easy to compose.

In plain language:

> HA Voice Memory stores what the assistant knows.
> Voice Assist Recall stores what was said.
> Identity Context tells the assistant who is speaking.
> The Context Engine decides what context matters right now.

## Runtime Workflow

A typical voice request should eventually flow like this:

```text
User speaks
  ↓
Wake word / Assist pipeline
  ↓
Speech-to-text
  ↓
Identity detection or metadata lookup
  ↓
Context Engine / adapter
  ├─ loads stable context from HA Voice Memory
  ├─ retrieves relevant prior context from Voice Assist Recall
  └─ adds current Home Assistant state if useful
  ↓
Selected AI conversation agent
  ↓
Text-to-speech response
  ↓
Voice Assist Recall saves the completed user/assistant exchange
  ↓
Session summary and candidate durable facts are updated later
```

## Current Phase

The current implementation is moving from Phase 1 into Phase 2.

Current household status: Voice Assist Recall is installed and has passed basic
testing.

The current implementation provides:

- local Home Assistant storage
- saved user/assistant turns
- metadata fields for speaker/person/device/room/agent
- `save_turn` service
- `recall` service
- `build_context` service
- `prepare_recall_context` service
- `save_session_summary` service
- `search_sessions` service
- Assist adapter conversation entity
- memory count sensor

This is a good foundation for two-tier recall. Session summaries are stored and
searched explicitly, but they are not generated automatically yet.

The current implementation also exposes a prompt-safe recall preparation
service. `conversation_memory.prepare_recall_context` returns whether relevant
prior context was found, a concise context block, and counts for summaries and
raw turns used. It is intended for Assist adapters, scripts, or future helper
sensors that decide whether to add recall to the current AI prompt.

The current Assist adapter can forward a request to a configured downstream
conversation agent. It calls `prepare_recall_context` for the current user text
and appends relevant recall through Home Assistant's `extra_system_prompt`
conversation field before forwarding.

Current retention policy:

- raw turns: 90 days by default, configurable
- session summaries: 365 days by default, configurable
- topic summaries: future tier, indefinite by default

## Target Memory Model

Voice Assist Recall should evolve toward a two-tier recall model.

### Tier 1: Raw Turns

Raw turns are exact user/assistant exchanges.

They are useful for:

- detailed lookup
- audit/debugging
- supporting evidence behind summaries
- reconstructing a prior session

A raw turn should include at least:

```text
turn_id
session_id
conversation_id
created_at
role or user/assistant fields
user_text
assistant_text
speaker_id
person_id
device_id
room_id
agent_id
```

The current `MemoryTurn` model is the start of this tier.

### Tier 2: Session Summaries

Session summaries are compact summaries of a group of turns.

They are useful for:

- fast recall
- prompt injection without excessive token use
- continuing long-running work
- answering “what did we discuss” questions

A session summary should include at least:

```text
session_id
started_at
ended_at
speaker_id
person_id
device_id
room_id
agent_id
title
summary
topics
importance
related_turn_ids
```

### Future Tier: Topic Summaries

Topic summaries can be added after session summaries.

They should summarize long-running topics across many sessions, such as:

- Home Assistant AI memory architecture
- speaker recognition
- Twilio voice assistant
- wake word training
- latency optimization

Topic summaries should be updated carefully and should cite or link back to source sessions where possible.
Topic summaries should be retained indefinitely by default unless a future
explicit retention policy changes that.

### Future Tier: Memory Candidates

Voice Assist Recall should eventually identify candidate facts that may deserve promotion into HA Voice Memory.

Examples:

- Eric chose the public project name Voice Assist Recall.
- Eric prefers short spoken assistant responses.
- A specific room/device mapping was confirmed.

Promotion should be deliberate. Voice Assist Recall may suggest durable facts, but HA Voice Memory should remain the curated stable-memory layer.

## Service-First Design

The project should remain service-first.

Core services should be callable by:

- Assist adapters
- custom conversation agents
- automations
- scripts
- speaker recognition integrations
- future LLM wrappers
- Twilio or phone-call adapters

The conversation platform should remain an adapter surface, not the only
integration path. The service API remains the reusable boundary for scripts,
automations, other adapters, and speaker-recognition projects.

Current services:

```text
conversation_memory.save_turn
conversation_memory.recall
conversation_memory.build_context
conversation_memory.prepare_recall_context
conversation_memory.save_session_summary
conversation_memory.search_sessions
```

Potential future services:

```text
conversation_memory.save_session_summary
conversation_memory.get_session
conversation_memory.search_sessions
conversation_memory.build_context
conversation_memory.prepare_recall_context
conversation_memory.suggest_memory_candidates
conversation_memory.mark_candidate_promoted
```

If/when the integration is renamed, equivalent `voice_assist_recall.*` services should be considered.

## Build Context Behavior

`build_context` should eventually prefer compact summaries before raw turns.

Recommended behavior:

1. Search scoped session summaries first.
2. Search raw turns second as supporting detail.
3. Return prompt-ready text that is concise and clearly labeled.
4. Include enough metadata for an adapter to decide whether the context is relevant.
5. Avoid dumping excessive raw transcript into the AI prompt.

A future prompt-ready context could look like:

```text
Relevant previous conversation summaries:
- Eric decided that HA Voice Memory and Voice Assist Recall should remain separate modules connected by a Context Engine.
- Voice Assist Recall should add session summaries before embeddings.

Relevant supporting turns:
- User: “Should HA Voice Memory and Voice Assist Recall be combined?”
- Assistant: “No, keep them separate but composable.”
```

## Assist Prompt and Helper Contract

The Home Assistant OpenAI Conversation Agent prompt has a practical character
limit, so the prompt should stay short and route to helper entities and memory
sensors rather than embedding long policy text directly.

Home Assistant `input_text` helpers should be treated as short policy/context
summaries, not durable memory stores and not large policy documents.

Current helper intent:

- `input_text.house_context`: short identity and operating context for the
  household assistant.
- `input_text.house_personality`: short style and tone policy.
- `input_text.house_security_definition`: short privacy, truthfulness, and memory
  safety policy.

The current Assist prompt should pull together:

- short helper policies from Home Assistant helpers
- stable memory from `sensor.house_memory_summary` attributes
- later, only selective prompt-ready recall from Voice Assist Recall

Current prompt pattern:

```jinja2
You are Elspeth, the voice of the Goforth house.

House context:
{{ states('input_text.house_context') }}

House personality:
{{ states('input_text.house_personality') }}

House security definition:
{{ states('input_text.house_security_definition') }}

Persistent house memory:
{{ state_attr('sensor.house_memory_summary', 'house') }}

Eric profile:
{{ state_attr('sensor.house_memory_summary', 'eric') }}

Shelley profile:
{{ state_attr('sensor.house_memory_summary', 'shelley') }}

Shared household preferences:
{{ state_attr('sensor.house_memory_summary', 'shared_preferences') }}

Use memory when relevant. Do not invent facts. Keep replies concise, truthful,
natural, and in plain text.
```

When Voice Assist Recall exposes a selective, prompt-ready recall sensor or
service result, the prompt may add a small section such as:

```jinja2
Relevant conversation recall:
{{ states('sensor.conversation_memory_relevant_recall') }}
```

Do not inject raw conversation history into the prompt by default. Recall context
must be filtered, concise, clearly labeled, and relevant to the current request.
If recall is not relevant, the prompt should omit it.

Current prompt-safe service behavior:

- `prepare_recall_context` searches session summaries first.
- If no summary matches, it can fall back to a small number of raw turns.
- If summaries match, supporting raw turns are omitted unless explicitly
  requested with `include_turns`.
- The response includes `relevant`, `context`, `summary_count`, and
  `turn_count`.
- The returned context is capped by `max_length`.

## Storage Direction

The current Home Assistant storage approach is acceptable for the prototype.

Raw turns and session summaries are pruned by configurable retention windows.
Topic summaries are intended to be retained indefinitely by default.

Current storage concern:

- The prototype store is scoped by Home Assistant config entry ID.
- Removing and re-adding the integration may create a new entry ID and leave
  prior memory data under an old storage key.
- This is acceptable during early testing, but it is not durable enough for the
  long-term goal of ChatGPT-like recall across sessions and maintenance events.

As the project grows, consider whether to keep using Home Assistant storage or migrate to a more structured local backend.

Potential path:

1. Home Assistant Store for Phase 1.
2. Stable domain-level storage identity or migration layer that can recover
   older entry-scoped stores.
3. Structured internal models for sessions and summaries.
4. SQLite for larger installations or long-term history.
5. Optional embeddings/vector search later, not now.

Migration requirements:

- Preserve raw turns, session summaries, and future topic summaries.
- Avoid accidental data merges if multiple config entries exist.
- Provide backup/export guidance before any storage migration.
- Add tests that prove old entry-scoped data can be loaded or migrated.

Do not implement embeddings before the basic session and summary model is stable.

## Privacy and Locality

Voice Assist Recall should be local-first.

The integration should not send conversation history to an external provider by itself.

Adapters may choose to include selected recall context in prompts sent to an AI provider, but that should be explicit and controlled by the user’s selected Assist/LLM pipeline.

## Naming Guidance

Use generic, community-friendly naming in code and docs.

Avoid hard-coding private household terms such as:

- Elspeth
- Goforth House
- Eric
- Shelley

Those names may appear in examples only when clearly marked as examples. The integration itself should support any assistant, household, or user setup.

## Backward Compatibility

While the project is early, breaking changes are acceptable if they simplify the public design before release.

Once the integration is shared more broadly, service names, storage migrations, and config entry behavior should be treated more carefully.

The possible rename from `conversation_memory` to `voice_assist_recall` should happen early if it is going to happen.

## Codex Working Guidelines

When Codex works on this repository, it should:

1. Read this file first.
2. Preserve the separation between Voice Assist Recall and HA Voice Memory.
3. Keep the integration provider-neutral.
4. Avoid coupling the backend to one LLM provider.
5. Treat the included conversation agent as optional/demo functionality.
6. Prefer small, testable implementation steps.
7. Add or update tests with architectural changes.
8. Avoid adding embeddings until raw turns and session summaries are stable.
9. Keep public/community naming generic.
10. Update this file when architectural decisions change.
11. Preserve the Assist prompt/helper contract unless Eric intentionally changes
    it.

## ChatGPT Working Guidelines

When ChatGPT reviews this project with Eric, it should:

1. Use this file as the shared architecture baseline.
2. Help Eric clarify project goals, boundaries, naming, and priority.
3. Recommend implementation direction for Codex without assuming code is complete.
4. Keep the broader Home Assistant voice AI architecture in view.
5. Identify when a decision belongs in HA Voice Memory, Voice Assist Recall, Identity Context, or the Context Engine.
6. Suggest updates to this file when project direction changes.

## Immediate Recommended Roadmap

### Phase 1: Current Prototype

- Save and recall raw turns.
- Preserve identity/source metadata.
- Provide `save_turn`, `recall`, and `build_context` services.
- Keep the conversation platform as an adapter surface, not the core dependency.

### Phase 2: Rename and Session Model

Decide whether to rename now:

- repository: `conversation-memory` → `voice-assist-recall`
- integration name: `Conversation Memory` → `Voice Assist Recall`
- domain: `conversation_memory` → `voice_assist_recall`

Then add:

- session model
- session creation/update behavior
- session summary storage
- tests for session-scoped recall

Current status:

- raw turns include `turn_id` and `session_id`
- session summary storage exists
- `save_session_summary` and `search_sessions` services exist
- `build_context` searches session summaries before raw turns
- automatic summary generation is not implemented

### Phase 3: Two-Tier Build Context

Update `build_context` so it can use:

1. relevant session summaries
2. supporting raw turns

The result should be concise enough to safely prepend to a voice assistant prompt.

Current status:

- `build_context` uses session summaries first and supporting raw turns second
- ranking, stronger limits, and summary/turn balancing still need refinement

### Phase 4: Prompt-Ready Recall Integration

Expose a selective, concise recall result that an Assist adapter or prompt helper
can include only when relevant. Do not expose raw history as a default prompt
block.

Current status:

- `conversation_memory.prepare_recall_context` exists as a response-only
  service.
- A first-pass Assist adapter exists.
- The adapter forwards to a configured downstream conversation agent.
- The adapter includes recall only when `prepare_recall_context` reports
  `relevant` true.
- The adapter saves completed user/assistant turns after the downstream response.
- Testing still needs to validate the adapter against the target Home Assistant
  version and the selected downstream AI agent.

### Phase 5: Topic Summaries

Add topic summaries for long-running subjects after session summaries work well.

Before or alongside topic summaries, design the storage migration path so
long-lived summaries survive integration remove/re-add and future backend
changes.

### Phase 6: Promotion Candidates

Add a way for Voice Assist Recall to suggest durable facts that may belong in HA Voice Memory.

### Phase 7: Optional Advanced Search

Only after the above is stable, consider:

- keyword ranking improvements
- recency weighting
- importance weighting
- SQLite storage
- optional embeddings/vector search

## Current Architectural Decision

Do not combine HA Voice Memory and Voice Assist Recall into one project right now.

Instead:

1. Keep HA Voice Memory as the curated stable-memory layer.
2. Build Voice Assist Recall as the conversation-history and recall layer.
3. Let Identity Context provide speaker/person metadata.
4. Build or adapt a Context Engine that reads from both memory layers.
5. Allow Voice Assist Recall to suggest durable facts for HA Voice Memory later.
6. Keep the Assist prompt short by using helper entities and filtered memory
   sensors/service results.

This preserves clean boundaries while still supporting the overall goal: a Home Assistant voice AI that can know who is speaking, remember durable household context, and refer back to previous conversations naturally.
