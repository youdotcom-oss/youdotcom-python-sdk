

from __future__ import annotations
from enum import Enum


class SafeSearch(str, Enum):
    r"""Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not."""

    OFF = "off"
    MODERATE = "moderate"
    STRICT = "strict"
