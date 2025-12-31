"""Example Usage of Structured Logger"""
from structured_logger import StructuredLogger

# Initialize logger for player P01
logger = StructuredLogger("player:P01")

# Log received message
logger.info(
    "Received game invitation",
    message_type="GAME_INVITATION",
    conversation_id="conv-12345",
    data={"match_id": "R1M1", "opponent": "P02"}
)

# Log error
logger.error(
    "Failed to connect to referee",
    data={"endpoint": "http://localhost:8001", "error": "timeout"}
)

# Expected output (JSON lines):
# {"timestamp": "2025-01-15T10:30:00.123Z",
#  "level": "INFO",
#  "agent_id": "player:P01",
#  "message": "Received game invitation",
#  "message_type": "GAME_INVITATION",
#  "conversation_id": "conv-12345",
#  "data": {"match_id": "R1M1", "opponent": "P02"}}
