

from __future__ import annotations
from enum import Enum


class ContentsFormats(str, Enum):
    HTML = "html"
    MARKDOWN = "markdown"
    METADATA = "metadata"  # Deprecated; will be removed in a future major release.
