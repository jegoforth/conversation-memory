"""Constants for Voice Assist Recall."""

DOMAIN = "conversation_memory"
STORAGE_KEY = f"{DOMAIN}.memories"
STORAGE_VERSION = 1

CONF_NAME = "name"
CONF_ADAPTER_CONTEXT_MAX_LENGTH = "adapter_context_max_length"
CONF_ADAPTER_INCLUDE_TURNS = "adapter_include_turns"
CONF_MAX_TURNS = "max_turns"
CONF_RECALL_TURNS = "recall_turns"
CONF_RAW_TURN_RETENTION_DAYS = "raw_turn_retention_days"
CONF_SESSION_SUMMARY_RETENTION_DAYS = "session_summary_retention_days"
CONF_TARGET_AGENT_ID = "target_agent_id"

ATTR_AGENT_ID = "agent_id"
ATTR_ASSISTANT_TEXT = "assistant_text"
ATTR_CONTEXT = "context"
ATTR_CONVERSATION_ID = "conversation_id"
ATTR_DEVICE_ID = "device_id"
ATTR_ENDED_AT = "ended_at"
ATTR_IMPORTANCE = "importance"
ATTR_INCLUDE_TURNS = "include_turns"
ATTR_LIMIT = "limit"
ATTR_MAX_LENGTH = "max_length"
ATTR_MEMORIES = "memories"
ATTR_PERSON_ID = "person_id"
ATTR_QUERY = "query"
ATTR_RELEVANT = "relevant"
ATTR_RELATED_TURN_IDS = "related_turn_ids"
ATTR_ROOM_ID = "room_id"
ATTR_SESSION_ID = "session_id"
ATTR_SESSION_SUMMARIES = "session_summaries"
ATTR_SPEAKER_ID = "speaker_id"
ATTR_STARTED_AT = "started_at"
ATTR_SUMMARY = "summary"
ATTR_SUMMARY_COUNT = "summary_count"
ATTR_TITLE = "title"
ATTR_TOPICS = "topics"
ATTR_TURN_COUNT = "turn_count"
ATTR_TURN_ID = "turn_id"
ATTR_USER_TEXT = "user_text"

DEFAULT_NAME = "Voice Assist Recall"
DEFAULT_ADAPTER_CONTEXT_MAX_LENGTH = 1200
DEFAULT_ADAPTER_INCLUDE_TURNS = False
DEFAULT_MAX_TURNS = 500
DEFAULT_PREPARED_CONTEXT_MAX_LENGTH = 1200
DEFAULT_RECALL_TURNS = 5
DEFAULT_RAW_TURN_RETENTION_DAYS = 90
DEFAULT_SESSION_SUMMARY_RETENTION_DAYS = 365

SERVICE_BUILD_CONTEXT = "build_context"
SERVICE_PREPARE_RECALL_CONTEXT = "prepare_recall_context"
SERVICE_RECALL = "recall"
SERVICE_SAVE_SESSION_SUMMARY = "save_session_summary"
SERVICE_SAVE_TURN = "save_turn"
SERVICE_SEARCH_SESSIONS = "search_sessions"
