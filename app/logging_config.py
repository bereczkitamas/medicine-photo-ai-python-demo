import logging
import os


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get(
    "LOG_FORMAT",
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


def configure_logging() -> None:
    # Avoid adding duplicate handlers if called multiple times (e.g., tests)
    root = logging.getLogger()
    if any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        # Still update level/format on existing stream handlers
        root.setLevel(LOG_LEVEL)
        for h in root.handlers:
            if isinstance(h, logging.StreamHandler):
                h.setLevel(LOG_LEVEL)
                h.setFormatter(logging.Formatter(LOG_FORMAT))
        return

    handler = logging.StreamHandler()
    handler.setLevel(LOG_LEVEL)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root.setLevel(LOG_LEVEL)
    root.addHandler(handler)


__all__ = ["configure_logging"]
