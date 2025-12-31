"""Retry with Exponential Backoff"""
import time
import requests
from typing import Optional, Dict, Any

class RetryConfig:
    MAX_RETRIES = 3
    BASE_DELAY = 2.0  # seconds
    BACKOFF_MULTIPLIER = 2.0

def call_with_retry(endpoint: str, method: str, 
                    params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send MCP request with retry logic.
    Uses exponential backoff between retries.
    
    Args:
        endpoint: Server endpoint URL
        method: Method name
        params: Parameters dictionary
        
    Returns:
        Response JSON or error dictionary
    """
    last_error = None
    for attempt in range(RetryConfig.MAX_RETRIES):
        try:
            response = requests.post(
                endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1
                },
                timeout=30
            )
            return response.json()
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            if attempt < RetryConfig.MAX_RETRIES - 1:
                delay = RetryConfig.BASE_DELAY * \
                    (RetryConfig.BACKOFF_MULTIPLIER ** attempt)
                time.sleep(delay)
    
    return {
        "error": {
            "error_code": "E005",
            "error_description": f"Max retries exceeded: {last_error}"
        }
    }
