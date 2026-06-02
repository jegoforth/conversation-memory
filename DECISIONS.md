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

- This is not yet a real session model. Phase 2 should add explicit session
  records with `started_at`, `ended_at`, title, summary, topics, importance, and
  related turn IDs.

### Build Context

The architecture says `build_context` should eventually prefer compact session
summaries before raw turns.

Decision for now:

- Keep `build_context` raw-turn based for Phase 1.
- Label the returned prompt context as Voice Assist Recall context.

Concern:

- Raw transcript context can become too large for voice assistant prompts. Once
  session summaries exist, `build_context` should search summaries first and use
  raw turns only as supporting detail.

### Storage Backend

Home Assistant Store remains acceptable for Phase 1.

Concern:

- Long-term history, session summaries, and future search features may justify a
  structured backend such as SQLite. Embeddings should wait until raw turns and
  summaries are stable.
