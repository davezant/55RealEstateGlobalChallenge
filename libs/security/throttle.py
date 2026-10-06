import threading
import time
from collections import defaultdict, deque

class LoginThrottle:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.failures: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def prune(self, key: str, now: float) -> deque:
        attempts = self.failures[key]
        while attempts and now - attempts[0] > self.window_seconds:
            attempts.popleft()
        return attempts

    def is_blocked(self, key: str) -> bool:
        with self.lock:
            return len(self.prune(key, time.monotonic())) >= self.max_attempts

    def register_failure(self, key: str) -> None:
        with self.lock:
            now = time.monotonic()
            self.prune(key, now).append(now)

    def reset(self, key: str) -> None:
        with self.lock:
            self.failures.pop(key, None)

login_throttle = LoginThrottle()
