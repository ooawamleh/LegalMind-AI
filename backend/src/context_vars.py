# backend/src/context_vars.py
from contextvars import ContextVar

# This variable will hold the session_id for the duration of a single request
session_context = ContextVar("session_context", default=None)