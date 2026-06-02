"""Constants for Conversation Memory."""

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
ATTR_LIMIT = "limit"
ATTR_MEMORIES = "memories"
ATTR_PERSON_ID = "person_id"
ATTR_QUERY = "query"
ATTR_ROOM_ID = "room_id"
ATTR_SPEAKER_ID = "speaker_id"
ATTR_USER_TEXT = "user_text"

DEFAULT_NAME = "Conversation Memory"
DEFAULT_MAX_TURNS = 500
DEFAULT_RECALL_TURNS = 5

SERVICE_BUILD_CONTEXT = "build_context"
SERVICE_RECALL = "recall"
SERVICE_SAVE_TURN = "save_turn"
