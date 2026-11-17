"""Deliberate YouCode smoke fixture. Do not merge."""
from abc import ABC, abstractmethod


class TotalStrategy(ABC):
    @abstractmethod
    def total(self, values):
        ...


class SumTotalStrategy(TotalStrategy):
    def total(self, values):
        result = 0
        for value in values:
            result = result + value
        return result


class TotalStrategyFactory:
    def create(self):
        return SumTotalStrategy()


def average(values):
    total = TotalStrategyFactory().create().total(values)
    return total / len(values) - 1
