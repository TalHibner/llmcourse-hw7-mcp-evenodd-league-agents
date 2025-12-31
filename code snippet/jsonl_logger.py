"""JSON Lines Logger for MCP Agents"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

LOG_ROOT = Path("SHARED/logs")

class JsonLogger:
    """
    Logger that writes to JSON Lines (.jsonl) format.
    Each line in the log file is an independent JSON object.
    
    Benefits:
    - Efficient append-only writes
    - Standard tools can read/parse
    - Real-time log streaming support
    """
    
    def __init__(self, component: str, league_id: Optional[str] = None):
        self.component = component
        
        # Determine log directory
        if league_id:
            subdir = LOG_ROOT / "league" / league_id
        else:
            subdir = LOG_ROOT / "system"
        
        subdir.mkdir(parents=True, exist_ok=True)
        self.log_file = subdir / f"{component}.log.jsonl"
    
    def log(self, event_type: str, level: str = "INFO", **details):
        """Write a log entry to JSONL file."""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component": self.component,
            "event_type": event_type,
            "level": level,
            **details,
        }
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # Convenience methods for different log levels
    def debug(self, event_type: str, **details):
        """Log at DEBUG level."""
        self.log(event_type, level="DEBUG", **details)
    
    def info(self, event_type: str, **details):
        """Log at INFO level."""
        self.log(event_type, level="INFO", **details)
    
    def warning(self, event_type: str, **details):
        """Log at WARNING level."""
        self.log(event_type, level="WARNING", **details)
    
    def error(self, event_type: str, **details):
        """Log at ERROR level."""
        self.log(event_type, level="ERROR", **details)
    
    def log_message_sent(self, message_type: str, recipient: str, **details):
        """Log a sent message."""
        self.debug("MESSAGE_SENT", 
                  message_type=message_type,
                  recipient=recipient, 
                  **details)
