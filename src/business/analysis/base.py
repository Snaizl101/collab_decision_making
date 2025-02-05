from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LLMClientInterface(ABC):
    """Interface for LLM API used by analysis module"""

    @abstractmethod
    async def analyze_topics(self, text: str, **kwargs) -> Dict[str, Any]:
        """Analyze text for topics using LLM"""
        pass

    @abstractmethod
    async def extract_hierarchies(self, topics: List[str], context: str) -> Dict[str, Any]:
        """Extract topic hierarchies and relationships"""
        pass
