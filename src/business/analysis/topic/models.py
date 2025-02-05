from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Topic:
    """Represents an identified topic"""
    name: str
    start_time: float
    end_time: float
    importance_score: float
    topic_id: Optional[int] = None
    subtopics: List['Topic'] = None
    parent_topic: Optional[str] = None


@dataclass
class TopicAnalysisResult:
    """Results from topic analysis"""
    topics: List[Topic]
    hierarchy: Dict[str, List[str]]
    timestamp: datetime = field(default_factory=datetime.now)
