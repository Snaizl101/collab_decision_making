from typing import Dict, Any, List
from pathlib import Path
import os
import json
import yaml
from together import Together
from pydantic import BaseModel, Field
from .base import LLMClientInterface
from .exceptions import LLMAPIError


# Topic-related schemas
class TopicSchema(BaseModel):
    name: str = Field(description="The name or title of the discussed topic")
    start_time: float = Field(description="When the topic discussion started (in seconds)")
    end_time: float = Field(description="When the topic discussion ended (in seconds)")


class TopicsResponse(BaseModel):
    topics: List[TopicSchema] = Field(description="List of topics identified in the discussion")


class HierarchyResponse(BaseModel):
    hierarchy: Dict[str, List[str]] = Field(
        description="Topic hierarchy with parent topics as keys and lists of child topics as values"
    )


class TogetherLLMClient(LLMClientInterface):
    """Together.ai API client with JSON mode"""

    def __init__(self, config_path: Path = Path("config/config.yaml")):
        with open(config_path) as f:
            config = yaml.safe_load(f)
            self.model = config["llm"]["model"]
            api_key = os.getenv("TOGETHER_API_KEY") or config["llm"]["together_api_key"]

        os.environ["TOGETHER_API_KEY"] = api_key
        self.client = Together()

    async def analyze_topics(self, text: str, **kwargs) -> Dict[str, Any]:
        """Analyze text for topics using LLM with JSON mode"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the discussion transcript and identify main topics. Respond only in JSON format."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.1,
                response_format={
                    "type": "json_object",
                    "schema": TopicsResponse.model_json_schema()
                }
            )
            return response

        except Exception as e:
            raise LLMAPIError(f"Topic analysis failed: {str(e)}")

    async def extract_hierarchies(self, topics: List[str], context: str) -> Dict[str, Any]:
        """Extract topic hierarchies with JSON mode"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the topics and identify hierarchical relationships. Respond only in JSON format."
                    },
                    {
                        "role": "user",
                        "content": f"Topics: {', '.join(topics)}\nContext: {context}"
                    }
                ],
                temperature=0.1,
                response_format={
                    "type": "json_object",
                    "schema": HierarchyResponse.model_json_schema()
                }
            )
            return response

        except Exception as e:
            raise LLMAPIError(f"Hierarchy extraction failed: {str(e)}")

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using LLM with JSON mode"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Analyze the sentiment of the text. Return a sentiment score between -1 (very negative) and 1 (very positive), and a confidence score between 0 and 1. Respond only in JSON format."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.1,
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sentiment_score": {"type": "number", "minimum": -1, "maximum": 1}
                        },
                        "required": ["sentiment_score"]
                    }
                }
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            raise LLMAPIError(f"Sentiment analysis failed: {str(e)}")

    async def close(self):
        """Nothing to close for Together client"""
        pass
