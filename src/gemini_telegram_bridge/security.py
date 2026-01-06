from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class SecurityMode(str, Enum):
    SAFE = "safe"
    BALANCED = "balanced"
    POWER = "power"

    @classmethod
    def from_value(cls, value: str) -> "SecurityMode":
        normalized = value.strip().lower()
        for mode in cls:
            if mode.value == normalized:
                return mode
        raise ValueError(f"Unsupported SECURITY_MODE: {value}")


@dataclass(slots=True)
class AccessController:
    allowed_ids: set[int]
    admin_ids: set[int]
    default_mode: SecurityMode

    def is_allowed(self, user_id: int) -> bool:
        return user_id in self.admin_ids or user_id in self.allowed_ids

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def resolve_mode(self, user_id: int, requested_mode: str | None) -> SecurityMode:
        if not requested_mode:
            return self.default_mode
        mode = SecurityMode.from_value(requested_mode)
        if mode is SecurityMode.POWER and not self.is_admin(user_id):
            raise PermissionError("POWER mode is restricted to admin users.")
        return mode

    def ensure_allowed(self, user_id: int) -> None:
        if not self.is_allowed(user_id):
            raise PermissionError("This Telegram user is not allowed to use the bridge.")

    def allow_shell(self, user_id: int, mode: SecurityMode) -> bool:
        if mode is SecurityMode.SAFE:
            return False
        if mode is SecurityMode.BALANCED:
            return True
        return self.is_admin(user_id)


@dataclass(slots=True)
class RateLimiter:
    limit: int
    window_seconds: int
    _entries: dict[int, deque[float]] = field(default_factory=dict)

    def allow(self, user_id: int) -> bool:
        now = time.monotonic()
        bucket = self._entries.setdefault(user_id, deque())
        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False
        bucket.append(now)
        return True
