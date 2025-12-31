"""MCP Tool Call Helper"""
import requests

def call_mcp_tool(endpoint, method, params):
    """
    Send a JSON-RPC request to an MCP server.
    
    Args:
        endpoint: Server endpoint URL
        method: Method name to call
        params: Parameters dictionary
        
    Returns:
        Response JSON
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(endpoint, json=payload)
    return response.json()
