# Decisions

This file records implementation concerns, tradeoffs, and architectural follow-up
items for Voice Assist Recall.

## 2026-06-03

### HACS Install Status

Voice Assist Recall was installed through HACS and tested in Home Assistant.

Progress:

- Added HACS metadata with `hacs.json`.
- Added `issue_tracker` to `manifest.json`.
- Tagged semantic HACS versions:
  - `v0.2.0`
  - `v0.2.1`
  - `v0.2.2`

Install issues found and fixed:

- HACS initially rejected commit-based version `9cb5be2`; fixed by adding HACS
  metadata and a semantic version tag.
- Home Assistant failed setup while importing the optional conversation platform;
  fixed in `0.2.1` by disabling `Platform.CONVERSATION` forwarding.
- `conversation_memory.recall` failed because `async_recall()` did not accept
  `conversation_id`; fixed in `0.2.2`.

### Service Test Results

Version `0.2.2` passed the first service-first test sequence in Home Assistant.

Confirmed working:

- `conversation_memory.save_turn`
- `conversation_memory.recall`
- `conversation_memory.save_session_summary`
- `conversation_memory.search_sessions`
- `conversation_memory.build_context`

Observed test result:

- Raw turn storage preserved `turn_id`, `session_id`, `conversation_id`,
  user/assistant text, and identity/source metadata.
- Raw turn recall worked with `session_id`.
- Session summary storage preserved title, summary, topics, importance,
  related turn IDs, and identity/source metadata.
- Session summary search worked with `session_id`.
- `build_context` returned session summaries before supporting raw turns.

Follow-up:

- Tighten prompt formatting to reduce extra blank lines in generated context.
- Keep the optional conversation agent disabled until the exact Home Assistant
  conversation entity API is validated against the target version.
- Continue broader testing with real Assist adapter metadata.

### Assist Prompt and Helper Contract

`ARCHITECTURE.md` now defines an Assist prompt/helper contract: keep the OpenAI
Conversation Agent prompt short, use helper entities for compact policy/context,
and include Voice Assist Recall output only when it is filtered and relevant.

Decision for now:

- Treat `conversation_memory.build_context` as an explicit service result for an
  adapter or script, not as an always-on prompt block.
- Do not inject raw conversation history into the default Assist prompt.
- Any future `sensor.conversation_memory_relevant_recall` should expose concise,
  query-relevant text only.

Concern:

- `build_context` currently returns session summaries plus supporting raw turns.
  This is acceptable for an explicit action call, but it should not be placed
  directly into a persistent prompt helper without relevance filtering and size
  limits.

### Retention Policy

The target behavior is ChatGPT-like previous-session recall without retaining
all raw transcript detail forever.

Decision:

- Raw turns default to 90 days retention.
- Session summaries default to 365 days retention.
- Both retention windows are configurable during setup.
- Expired raw turns and session summaries are pruned when the store loads or
  writes.
- Topic summaries are a future tier and should be retained indefinitely unless a
  later explicit policy changes that.

Concern:

- Config flow currently stores retention settings at setup time only. A future
  options flow should allow changing retention without removing/re-adding the
  integration.

### Prompt-Safe Recall Preparation

Home Assistant and the existing AI conversation agent do not automatically call
Voice Assist Recall. The storage and search services work, but AI access needs a
runtime bridge that prepares relevant prior context for the current request.

Decision:

- Add `conversation_memory.prepare_recall_context` as the next integration
  boundary.
- Return structured response metadata:
  - `relevant`
  - `context`
  - `summary_count`
  - `turn_count`
- Prefer session summaries over raw turns.
- Use raw turns only as a fallback when no summary matches, or when the caller
  explicitly sets `include_turns`.
- Limit returned context by `max_length`.

Concern:

- This still does not automatically inject memory into the selected AI
  conversation agent. A future Assist adapter, script, or helper entity must
  call `prepare_recall_context` per request and include the returned context
  only when `relevant` is true.

### Storage Migration Strategy Needed

During `0.4.0` testing, `conversation_memory.search_sessions` returned an empty
`session_summaries` list after reinstall/update testing. This suggests prior
test memory was unavailable to the current config entry.

Likely cause:

- The current Home Assistant Store key is scoped by `entry.entry_id`.
- Removing and re-adding the integration creates a new config entry ID.
- Memory stored under the old entry ID can become orphaned from the new
  integration instance.

Decision:

- Treat config-entry-scoped storage as acceptable for the early prototype, but
  not acceptable for a durable ChatGPT-like recall feature.
- Plan a storage migration strategy before broader release or before users rely
  on long-term memories.

Migration planning requirements:

- Choose a stable storage identity that survives remove/re-add where practical.
- Consider a domain-level storage key for the primary memory store instead of
  only `entry.entry_id` scoped storage.
- Add import/migration logic that can detect older entry-scoped stores and move
  turns and summaries into the new stable store.
- Avoid data loss when multiple config entries exist.
- Provide clear backup/export guidance before storage migrations.
- Add tests for loading old entry-scoped data and preserving raw turns, session
  summaries, and future topic summaries.

Concern:

- A storage migration should be designed carefully before implementation. Moving
  too quickly could either ignore orphaned memories or merge data from separate
  intended instances incorrectly.

## 2026-06-02

### Public Name vs Integration Domain

The architecture establishes **Voice Assist Recall** as the public project name.
The repository is still `conversation-memory`, and the Home Assistant domain is
still `conversation_memory`.

Decision for now:

- Update user-facing names to Voice Assist Recall.
- Keep `conversation_memory.*` services and `custom_components/conversation_memory`
  for the current prototype.

Concern:

- If the project is renamed to `voice-assist-recall` / `voice_assist_recall`, it
  should happen before wider HACS/community release. Renaming later will require
  a migration plan for config entries, storage keys, service names, HACS metadata,
  and documentation.

### Session Model

The architecture calls for raw turns first, then session summaries.

Decision for now:

- Add `turn_id` and `session_id` to raw turns.
- Default `session_id` to `conversation_id` when no explicit session is provided.
- Allow services to save and filter by `session_id`.

Concern:

- Session summaries are now stored, but they are explicitly written by callers
  through `conversation_memory.save_session_summary`. The integration does not
  generate summaries automatically yet.
- A future session model may still need explicit session records separate from
  summaries if lifecycle tracking becomes important.

### Build Context

The architecture says `build_context` should eventually prefer compact session
summaries before raw turns.

Decision for now:

- `build_context` searches session summaries first.
- Raw turns are included as supporting detail after summaries.
- Label the returned prompt context as Voice Assist Recall context.

Concern:

- Raw transcript context can still become too large for voice assistant prompts.
  The next refinement should add stronger limits and ranking between summaries
  and supporting turns.

### Storage Backend

Home Assistant Store remains acceptable for Phase 1.

Concern:

- Long-term history, session summaries, and future search features may justify a
  structured backend such as SQLite. Embeddings should wait until raw turns and
  summaries are stable.

### Optional Conversation Agent

The optional conversation platform caused setup failure during the first HACS
install test because Home Assistant failed while importing `conversation.py`.

Decision for now:

- Disable `Platform.CONVERSATION` forwarding.
- Keep the service-first backend and memory count sensor installable.
- Test `save_turn`, `recall`, `save_session_summary`, `search_sessions`, and
  `build_context` first.

Concern:

- The demo conversation agent should only be re-enabled after validating the
  exact conversation entity API against the target Home Assistant version.
