

from __future__ import annotations
from enum import Enum


class Freshness(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
