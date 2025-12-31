"""
Structured JSON Lines (JSONL) logger for MCP league system.

Provides consistent logging across all agents with proper formatting.
"""

import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class LogLevel(str, Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class JsonLogger:
    """
    JSONL logger for structured logging.

    Each log entry is a single JSON object per line for efficient streaming and parsing.
    """

    def __init__(self, component: str, league_id: Optional[str] = None):
        """
        Initialize logger.

        Args:
            component: Component identifier (e.g., "player:P01", "referee:REF01")
            league_id: Optional league ID for league-specific logs
        """
        self.component = component
        self.league_id = league_id
        self.log_file = self._get_log_file_path()

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> Path:
        """Determine log file path based on component type"""
        base_path = Path("SHARED/logs")

        if self.component.startswith("league_manager"):
            if self.league_id:
                return base_path / "league" / self.league_id / "league.log.jsonl"
            return base_path / "system" / "league_manager.log.jsonl"
        elif ":" in self.component:
            # Agent format: "player:P01" or "referee:REF01"
            agent_id = self.component.split(":")[-1]
            return base_path / "agents" / f"{agent_id}.log.jsonl"
        else:
            return base_path / "system" / f"{self.component}.log.jsonl"

    def _write_log(self, level: LogLevel, event_type: str, details: Dict[str, Any]) -> None:
        """Write log entry to file"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": self.component,
            "event_type": event_type,
            "level": level.value,
            "details": details,
        }

        # Write as single line JSON
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            f.flush()  # Ensure immediate write

    def debug(self, event_type: str, **details) -> None:
        """Log DEBUG level message"""
        self._write_log(LogLevel.DEBUG, event_type, details)

    def info(self, event_type: str, **details) -> None:
        """Log INFO level message"""
        self._write_log(LogLevel.INFO, event_type, details)

    def warning(self, event_type: str, **details) -> None:
        """Log WARNING level message"""
        self._write_log(LogLevel.WARNING, event_type, details)

    def error(self, event_type: str, **details) -> None:
        """Log ERROR level message"""
        self._write_log(LogLevel.ERROR, event_type, details)

    def log_message_sent(self, message_type: str, recipient: str, **extra) -> None:
        """Convenience method for logging sent messages"""
        self.info(
            "MESSAGE_SENT",
            message_type=message_type,
            recipient=recipient,
            **extra
        )

    def log_message_received(self, message_type: str, sender: str, **extra) -> None:
        """Convenience method for logging received messages"""
        self.info(
            "MESSAGE_RECEIVED",
            message_type=message_type,
            sender=sender,
            **extra
        )

    def log_state_change(self, old_state: str, new_state: str, **extra) -> None:
        """Convenience method for logging state transitions"""
        self.info(
            "STATE_CHANGE",
            old_state=old_state,
            new_state=new_state,
            **extra
        )
