"""
Topic analyzer module.
Uses transcribed text to identify and structure discussion topics.
Uses LLM to extract topics and hierarchical relationships.
"""
from typing import List, Dict, Any
import json
import logging
from src.business.analysis.base import LLMClientInterface
from src.business.analysis.topic.models import Topic, TopicAnalysisResult
from src.business.analysis.exceptions import TopicAnalysisError, ValidationError
from src.business.audio.models import TranscriptionSegment

class TopicAnalyzer:
    """Analyzes discussion transcripts to identify and structure topics.

    Capabilities:
    - Extract main discussion topics
    - Track topic progression
    - Associate topics with timestamps

    Uses LLM for:
    - Topic identification
    """

    def __init__(self, llm_client: LLMClientInterface):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)

    async def analyze(self, transcription_segments: List[Dict[str, Any]]) -> TopicAnalysisResult:
        """
        Analyze transcription segments to identify topics and their relationships.

        Args:
            transcription_segments: List of transcription segments from the audio processor

        Returns:
            TopicAnalysisResult containing identified topics and their hierarchy
        """
        try:
            # Combine segments into full text while preserving timing
            full_text = self._prepare_text(transcription_segments)

            # Log input to LLM
            self.logger.debug(f"Sending to LLM: {full_text}")

            # Get initial topics from LLM
            llm_response = await self.llm_client.analyze_topics(full_text)

            # Debug logging
            self.logger.debug(f"Raw LLM response: {llm_response}")

            topics = self._parse_topics(llm_response)

            # Extract topic hierarchies
            topic_names = [t.name for t in topics]
            hierarchy_response = await self.llm_client.extract_hierarchies(topic_names, full_text)
            hierarchy = self._parse_hierarchy(hierarchy_response)

            # Update topics with hierarchy information
            self._update_topic_relationships(topics, hierarchy)

            return TopicAnalysisResult(
                topics=topics,
                hierarchy=hierarchy
            )

        except Exception as e:
            self.logger.error(f"Topic analysis failed: {e}")
            raise TopicAnalysisError(f"Analysis failed: {str(e)}")

    def _prepare_text(self, segments: List[TranscriptionSegment]) -> str:
        """Prepare transcription segments for analysis"""
        return " ".join(
            f"[{segment.start:.2f}s] {segment.speaker}: {segment.text}"
            for segment in segments
        )

    def _parse_topics(self, llm_response: Any) -> List[Topic]:
        """Parse LLM response into Topic objects"""
        try:
            # Handle Together.ai ChatCompletionResponse format
            if hasattr(llm_response, 'choices'):
                content = llm_response.choices[0].message.content
            else:
                content = llm_response['choices'][0]['message']['content']

            data = json.loads(content)

            return [
                Topic(
                    name=t['name'],
                    start_time=float(t['start_time']),
                    end_time=float(t['end_time']),
                )
                for t in data['topics']
            ]
        except (KeyError, json.JSONDecodeError, AttributeError) as e:
            raise ValidationError(f"Failed to parse topics: {str(e)}")

    def _parse_hierarchy(self, llm_response: Any) -> Dict[str, List[str]]:
        """Parse LLM response into topic hierarchy"""
        try:
            # Handle Together.ai ChatCompletionResponse format
            if hasattr(llm_response, 'choices'):
                content = llm_response.choices[0].message.content
            else:
                content = llm_response['choices'][0]['message']['content']

            data = json.loads(content)
            return data['hierarchy']
        except (KeyError, json.JSONDecodeError, AttributeError) as e:
            raise ValidationError(f"Failed to parse hierarchy: {str(e)}")

    def _update_topic_relationships(self, topics: List[Topic], hierarchy: Dict[str, List[str]]) -> None:
        """Update topics with their hierarchical relationships"""
        topic_map = {t.name: t for t in topics}

        for parent, children in hierarchy.items():
            if parent in topic_map:
                parent_topic = topic_map[parent]
                parent_topic.subtopics = [
                    topic_map[child] for child in children
                    if child in topic_map
                ]

                for child in children:
                    if child in topic_map:
                        topic_map[child].parent_topic = parent