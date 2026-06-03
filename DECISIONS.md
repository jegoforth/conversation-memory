# Decisions

This file records implementation concerns, tradeoffs, and architectural follow-up
items for Voice Assist Recall.

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
