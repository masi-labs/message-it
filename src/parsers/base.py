from abc import ABC, abstractmethod
from typing import Any

class Parser(ABC):
    @staticmethod
    @abstractmethod
    def parse(value: str) -> Any:
        raise NotImplementedError
