"""
Context utilities to keep the current conversation identifiers stable across tool calls.
This prevents the LLM from hallucinating phone numbers or channels when invoking tools.
Uses ContextVar when available and a module-level fallback for thread hops.
"""
from contextvars import ContextVar
from typing import Optional, Tuple

# Per-thread conversation identifiers
_current_user_id: ContextVar[Optional[str]] = ContextVar("integrado_current_user_id", default=None)
_current_channel: ContextVar[Optional[str]] = ContextVar("integrado_current_channel", default=None)

# Fallback for cases where execution hops threads (crew internal workers)
_fallback_user_id: Optional[str] = None
_fallback_channel: Optional[str] = None


def set_current_session(user_id: str, channel: str) -> Tuple[object, object]:
    """Store the current conversation identifiers and return tokens to restore later."""
    global _fallback_user_id, _fallback_channel
    _fallback_user_id = user_id
    _fallback_channel = channel
    tok_user = _current_user_id.set(user_id)
    tok_chan = _current_channel.set(channel)
    return tok_user, tok_chan


def reset_current_session(tok_user: object, tok_chan: object) -> None:
    """Restore the previous conversation identifiers using the provided tokens."""
    global _fallback_user_id, _fallback_channel
    try:
        _current_user_id.reset(tok_user)
    except Exception:
        pass
    try:
        _current_channel.reset(tok_chan)
    except Exception:
        pass
    _fallback_user_id = None
    _fallback_channel = None


def current_user_id(default: Optional[str] = None) -> Optional[str]:
    """Get the active user_id for the current execution context."""
    val = _current_user_id.get(None)
    if val:
        return val
    if _fallback_user_id:
        return _fallback_user_id
    return default


def current_channel(default: Optional[str] = None) -> Optional[str]:
    """Get the active channel for the current execution context."""
    val = _current_channel.get(None)
    if val:
        return val
    if _fallback_channel:
        return _fallback_channel
    return default
