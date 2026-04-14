"""Base interface for language model clients."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Small interface to keep provider-specific code isolated."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response from the model."""
