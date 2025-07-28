# context_manager.py
import contextvars

context_var = contextvars.ContextVar("caller", default="cli")
