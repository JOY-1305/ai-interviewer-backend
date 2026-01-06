# app/middleware/rate_limit.py

import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window = 60  # seconds
        self.requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit public endpoints
        if request.url.path.startswith("/public"):
            ip = request.client.host
            now = time.time()

            # Remove old requests
            self.requests[ip] = [
                t for t in self.requests[ip]
                if now - t < self.window
            ]

            if len(self.requests[ip]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )

            self.requests[ip].append(now)

        return await call_next(request)
