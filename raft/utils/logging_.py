import typing as t

import structlog


class StructLogger(t.Protocol):
    def info(self, msg: str, *args: t.Any, **kwargs: t.Any) -> None: ...


_logger: StructLogger | None = None


def create_logger() -> StructLogger:
    """Create a logger for the raft package."""
    global _logger
    if _logger is None:
        _logger = structlog.get_logger()
    assert _logger is not None
    return _logger
