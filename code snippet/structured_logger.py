"""Structured Logging for MCP Agents"""
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any

class StructuredLogger:
    """
    JSON-based structured logger for MCP protocol compliance.
    All log entries are output as JSON lines.
    """
    LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]
    
    def __init__(self, agent_id: str, min_level: str = "INFO"):
        self.agent_id = agent_id
        self.min_level = self.LEVELS.index(min_level)
    
    def log(self, level: str, message: str,
            message_type: Optional[str] = None,
            conversation_id: Optional[str] = None,
            data: Optional[Dict[str, Any]] = None):
        """Log a structured message"""
        if self.LEVELS.index(level) < self.min_level:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "agent_id": self.agent_id,
            "message": message
        }
        
        if message_type:
            log_entry["message_type"] = message_type
        if conversation_id:
            log_entry["conversation_id"] = conversation_id
        if data:
            log_entry["data"] = data
        
        print(json.dumps(log_entry), file=sys.stderr)
    
    def debug(self, message: str, **kwargs):
        self.log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.log("INFO", message, **kwargs)
    
    def warn(self, message: str, **kwargs):
        self.log("WARN", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log("ERROR", message, **kwargs)
