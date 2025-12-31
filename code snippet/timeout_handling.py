"""Request with Timeout Handling"""
import requests

def call_with_timeout(endpoint, method, params, timeout=30):
    """
    Make a JSON-RPC call with timeout handling.
    
    Args:
        endpoint: Server endpoint URL
        method: Method name
        params: Parameters dictionary
        timeout: Timeout in seconds (default: 30)
        
    Returns:
        Response JSON or error dictionary
    """
    try:
        response = requests.post(
            endpoint,
            json={
                "jsonrpc": "2.0", 
                "method": method,
                "params": params, 
                "id": 1
            },
            timeout=timeout
        )
        return response.json()
    except requests.Timeout:
        return {"error": "TIMEOUT"}
    except requests.RequestException as e:
        return {"error": str(e)}
