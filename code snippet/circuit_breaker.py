"""Circuit Breaker Pattern Implementation"""
from datetime import datetime, timedelta

class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are blocked
    - HALF_OPEN: Testing if service recovered, allow one request
    """
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if datetime.now() - self.last_failure > \
               timedelta(seconds=self.reset_timeout):
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # HALF_OPEN allows one try
    
    def record_success(self):
        """Record successful request"""
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed request"""
        self.failures += 1
        self.last_failure = datetime.now()
        if self.failures >= self.threshold:
            self.state = "OPEN"
