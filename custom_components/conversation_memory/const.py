"""Constants for Voice Assist Recall."""

DOMAIN = "conversation_memory"
STORAGE_KEY = f"{DOMAIN}.memories"
STORAGE_VERSION = 1

CONF_NAME = "name"
CONF_MAX_TURNS = "max_turns"
CONF_RECALL_TURNS = "recall_turns"

ATTR_AGENT_ID = "agent_id"
ATTR_ASSISTANT_TEXT = "assistant_text"
ATTR_CONTEXT = "context"
ATTR_CONVERSATION_ID = "conversation_id"
ATTR_DEVICE_ID = "device_id"
ATTR_ENDED_AT = "ended_at"
ATTR_IMPORTANCE = "importance"
ATTR_LIMIT = "limit"
ATTR_MEMORIES = "memories"
ATTR_PERSON_ID = "person_id"
ATTR_QUERY = "query"
ATTR_RELATED_TURN_IDS = "related_turn_ids"
ATTR_ROOM_ID = "room_id"
ATTR_SESSION_ID = "session_id"
ATTR_SESSION_SUMMARIES = "session_summaries"
ATTR_SPEAKER_ID = "speaker_id"
ATTR_STARTED_AT = "started_at"
ATTR_SUMMARY = "summary"
ATTR_TITLE = "title"
ATTR_TOPICS = "topics"
ATTR_TURN_ID = "turn_id"
ATTR_USER_TEXT = "user_text"

DEFAULT_NAME = "Voice Assist Recall"
DEFAULT_MAX_TURNS = 500
DEFAULT_RECALL_TURNS = 5

SERVICE_BUILD_CONTEXT = "build_context"
SERVICE_RECALL = "recall"
SERVICE_SAVE_SESSION_SUMMARY = "save_session_summary"
SERVICE_SAVE_TURN = "save_turn"
SERVICE_SEARCH_SESSIONS = "search_sessions"
