

from __future__ import annotations
from enum import Enum


class ReportVerbosity(str, Enum):
    r"""Select whether to receive a medium or high length model response."""

    MEDIUM = "medium"
    HIGH = "high"
