import pytest
import sys
import os
import asyncio
import yaml
import tempfile
from datetime import datetime
from pathlib import Path

# Class imports
from business.analysis.topic.analyzer import TopicAnalyzer
from storage.dao.sqlite.sqlite_dao import SQLiteDAO
from storage.dao.exceptions import DataIntegrityError, RecordNotFoundError
from presentation.reports.generators import HTMLReportGenerator
from business.analysis.argument.analyzer import ArgumentAnalyzer
from business.analysis.llm_client import TogetherLLMClient
from business.analysis.argument.models import Argument
from business.analysis.argument.models import DiscussionThread


pytestmark = pytest.mark.asyncio  # Add this line to mark all tests as async
sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'src'))


@pytest.mark.asyncio
async def test_topic_analyzer():
    """Test the topic analyzer with a simple transcription"""

    # Initialize with your API key
    llm_client = TogetherLLMClient(
        api_key="d17b86bc566294e187f01e25cf6ef58e9264567564ac4f9adb9ba9e5335ad4ba"
    )
    analyzer = TopicAnalyzer(llm_client)

    # Test with simple transcription
    transcription = [
        {
            "speaker_id": "speaker1",
            "start_time": 0,
            "end_time": 30,
            "text": "Let's discuss the quarterly budget. We need to review our expenses and plan for next quarter."
        },
        {
            "speaker_id": "speaker2",
            "start_time": 31,
            "end_time": 45,
            "text": "I agree. We should also consider our revenue projections."
        }
    ]

    result = await analyzer.analyze(transcription)

    # Print analysis results
    print("\n" + "=" * 50)
    print("ANALYSIS RESULTS")
    print("=" * 50)

    print("\nIDENTIFIED TOPICS:")
    for topic in result.topics:
        print(f"\n• Topic: {topic.name}")
        print(f"  Duration: {topic.start_time:.2f}s - {topic.end_time:.2f}s")
        print(f"  Importance: {topic.importance_score:.2f}")

    print("\nTOPIC HIERARCHY:")
    if result.hierarchy:
        for parent, children in result.hierarchy.items():
            print(f"\n• Parent Topic: {parent}")
            print("  Subtopics:")
            for child in children:
                print(f"    - {child}")
    else:
        print("  No hierarchical relationships found")

    print("\nSTATISTICS:")
    print(f"• Total topics identified: {len(result.topics)}")
    print(f"• Total hierarchical relationships: {len(result.hierarchy) if result.hierarchy else 0}")
    print("=" * 50)

    # Basic assertions
    assert result is not None
    assert hasattr(result, 'topics')
    assert hasattr(result, 'hierarchy')
    assert len(result.topics) > 0

    # Clean up
    await llm_client.close()


# Test file storage
def test_file_storage(tmp_path):
    from storage.files.local_storage import LocalFileStorage

    storage = LocalFileStorage(tmp_path)
    test_data = b"test audio data"

    # Write test file
    test_file = tmp_path / "test.wav"
    test_file.write_bytes(test_data)

    # Test storage
    file_id = storage.store_audio(test_file, "wav")
    assert file_id is not None

    # Test retrieval
    stored_path = storage.get_audio(file_id)
    assert stored_path.exists()


def test_sqlite_dao_comprehensive(tmp_path):
    """Test all major functionality of the SQLite DAO"""

    # Initialize DAO with test database
    db_path = tmp_path / "test.db"
    dao = SQLiteDAO(db_path)

    # Test Data
    recording_id = "test_recording_123"
    file_path = Path("test.wav")
    duration = 60
    recording_date = datetime.now()
    format_type = "wav"

    print("\n" + "=" * 50)
    print("DATABASE TEST RESULTS")
    print("=" * 50)

    # 1. Test Recording Storage and Retrieval
    print("\n1. Testing Recording Operations:")
    dao.store_recording(
        recording_id=recording_id,
        file_path=file_path,
        duration=duration,
        recording_date=recording_date,
        format=format_type
    )

    recording = dao.get_recording_metadata(recording_id)
    assert recording is not None
    assert recording["recording_id"] == recording_id
    assert recording["duration"] == duration
    assert recording["format"] == format_type
    print("✓ Recording storage and retrieval successful")

    # 2. Test Transcription Storage and Retrieval
    print("\n2. Testing Transcription Operations:")
    transcription_segments = [
        {
            "speaker_id": "speaker1",
            "start_time": 0.0,
            "end_time": 10.0,
            "text": "Hello, this is a test.",
        },
        {
            "speaker_id": "speaker2",
            "start_time": 10.0,
            "end_time": 20.0,
            "text": "Yes, this is a test response.",
        }
    ]

    dao.store_transcription(recording_id, transcription_segments)
    retrieved_segments = dao.get_transcription(recording_id)
    assert len(retrieved_segments) == 2
    assert retrieved_segments[0]["text"] == "Hello, this is a test."
    print("✓ Transcription storage and retrieval successful")

    # 3. Test Topic Storage and Retrieval
    print("\n3. Testing Topic Operations:")
    topic_data = {
        "topic_name": "Test Topic",
        "start_time": 0.0,
        "end_time": 30.0,
        "importance_score": 0.8
    }

    topic_id = dao.store_topic(recording_id, topic_data)
    topics = dao.get_topics(recording_id)
    assert len(topics) == 1
    assert topics[0]["topic_name"] == "Test Topic"
    print("✓ Topic storage and retrieval successful")

    # 4. Test Argument Storage and Retrieval
    print("\n4. Testing Argument Operations:")
    argument_data = {
        "speaker_id": "speaker1",
        "start_time": 5.0,
        "end_time": 15.0,
        "argument_text": "This is a test argument",
        "argument_type": "support",
        "conclusion": "Test conclusion"
    }

    argument_id = dao.store_argument(recording_id, topic_id, argument_data)
    arguments = dao.get_arguments(recording_id)
    assert len(arguments) == 1
    assert arguments[0]["argument_text"] == "This is a test argument"
    print("✓ Argument storage and retrieval successful")

    # 5. Test Agreement Storage and Retrieval
    print("\n5. Testing Agreement Operations:")
    agreement_data = {
        "speaker_id": "speaker2",
        "agreement_type": "agree",
        "timestamp": 16.0
    }

    agreement_id = dao.store_agreement(recording_id, argument_id, agreement_data)
    agreements = dao.get_agreements(recording_id)
    assert len(agreements) == 1
    assert agreements[0]["agreement_type"] == "agree"
    print("✓ Agreement storage and retrieval successful")

    # 6. Test Gap Storage and Retrieval
    print("\n6. Testing Gap Operations:")
    gap_data = {
        "gap_type": "missing_viewpoint",
        "description": "Need more perspective on this topic",
        "importance_score": 0.7
    }

    gap_id = dao.store_gap(recording_id, topic_id, gap_data)
    gaps = dao.get_gaps(recording_id)
    assert len(gaps) == 1
    assert gaps[0]["gap_type"] == "missing_viewpoint"
    print("✓ Gap storage and retrieval successful")

    # 7. Test Discussion Summary
    print("\n7. Testing Discussion Summary:")
    summary = dao.get_discussion_summary(recording_id)
    assert summary["metadata"] is not None
    assert len(summary["topics"]) == 1
    assert len(summary["arguments"]) == 1
    assert len(summary["agreements"]) == 1
    assert len(summary["gaps"]) == 1
    print("✓ Discussion summary retrieval successful")

    # 8. Test Error Cases
    print("\n8. Testing Error Cases:")
    # Test non-existent recording
    with pytest.raises(RecordNotFoundError):
        dao.get_recording_metadata("nonexistent_id")
    print("✓ Error handling successful")

    # Print final statistics
    print("\nFinal Statistics:")
    print(f"• Stored Recordings: 1")
    print(f"• Stored Transcription Segments: {len(retrieved_segments)}")
    print(f"• Stored Topics: {len(topics)}")
    print(f"• Stored Arguments: {len(arguments)}")
    print(f"• Stored Agreements: {len(agreements)}")
    print(f"• Stored Gaps: {len(gaps)}")
    print("=" * 50)


def test_dao_data_integrity(tmp_path):
    """Test data integrity constraints of the DAO"""
    dao = SQLiteDAO(tmp_path / "test.db")

    # Test duplicate recording ID
    recording_id = "test_recording_123"

    # First insertion should succeed
    dao.store_recording(
        recording_id=recording_id,
        file_path=Path("test.wav"),
        duration=60,
        recording_date=datetime.now(),
        format="wav"
    )

    # Verify the recording was stored
    stored_recording = dao.get_recording_metadata(recording_id)
    assert stored_recording is not None
    assert stored_recording["recording_id"] == recording_id

    # Attempt to insert duplicate should raise DataIntegrityError
    with pytest.raises(DataIntegrityError) as exc_info:
        dao.store_recording(
            recording_id=recording_id,
            file_path=Path("test2.wav"),
            duration=30,
            recording_date=datetime.now(),
            format="wav"
        )

    # Verify the error message contains useful information
    assert recording_id in str(exc_info.value)
    assert "already exists" in str(exc_info.value)

    # Verify the original recording wasn't modified
    stored_recording = dao.get_recording_metadata(recording_id)
    assert str(stored_recording["file_path"]) == "test.wav"


def test_report_generator():
    """Test the HTML report generator"""
    # Use the existing template directory
    template_dir = Path(__file__).parent.parent / "src" / "presentation" / "reports" / "templates"
    assert template_dir.exists(), f"Template directory not found at {template_dir}"

    # Create a permanent output directory in the project
    output_dir = Path(__file__).parent.parent / "test_output" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize generator
    generator = HTMLReportGenerator(template_dir)

    # Create test data
    test_data = {
        "topics": [
            {
                "name": "Budget Review",
                "start_time": 0,
                "end_time": 60,
                "importance_score": 0.8
            },
            {
                "name": "Project Timeline",
                "start_time": 61,
                "end_time": 120,
                "importance_score": 0.9
            }
        ],
        "transcription": [
            {
                "speaker_id": "Speaker1",
                "text": "Let's review the quarterly budget.",
                "start_time": 0,
                "end_time": 5
            },
            {
                "speaker_id": "Speaker2",
                "text": "I have the figures ready.",
                "start_time": 6,
                "end_time": 8
            }
        ],
        "metadata": {
            "recording_id": "test_123",
            "duration": 120,
            "date": datetime.now().isoformat()
        }
    }

    # Test successful report generation
    report_path = generator.generate(test_data, output_dir)
    print(f"\nReport generated at: {report_path}")

    # Verify the report was created
    assert report_path.exists()
    assert report_path.suffix == '.html'

    # Verify report content
    content = report_path.read_text()
    assert 'Budget Review' in content
    assert 'Project Timeline' in content
    assert 'Speaker1' in content
    assert 'Speaker2' in content


@pytest.fixture
def dummy_config(tmp_path, monkeypatch):
    """
    Create a temporary dummy config file for TogetherLLMClient.
    """
    dummy_config_data = {
        "llm": {
            "model": "dummy-model",
            "together_api_key": "dummy-key"
        }
    }
    config_file = tmp_path / "config.yaml"
    with config_file.open("w") as f:
        yaml.dump(dummy_config_data, f)
    # Also set the TOGETHER_API_KEY environment variable
    monkeypatch.setenv("TOGETHER_API_KEY", "dummy-key")
    return config_file


@pytest.mark.asyncio
async def test_argument_analyzer(dummy_config):
    """Test the argument analyzer with a simple set of arguments."""

    # Initialize the LLM client with the dummy config file
    llm_client = TogetherLLMClient(config_path=dummy_config)
    analyzer = ArgumentAnalyzer(llm_client)

    # Create test arguments.
    # Here we create a few dummy Argument objects.
    # Adjust the instantiation as needed based on your Argument model's constructor.
    arguments = [
        Argument(
            speaker_id="speaker1",
            timestamp=1.0,
            main_claim="We should increase the marketing budget.",
            argument_type="initial"
        ),
        Argument(
            speaker_id="speaker2",
            timestamp=2.0,
            main_claim="I disagree, the current budget is sufficient.",
            argument_type="counter"
        ),
        Argument(
            speaker_id="speaker3",
            timestamp=3.0,
            main_claim="Maybe we could reallocate funds from other areas instead.",
            argument_type="alternative"
        ),
    ]

    # For testing _build_threads, we need to simulate the analysis.
    # We'll call the analyze method of the ArgumentAnalyzer.
    # Note: This assumes that your LLM client (TogetherLLMClient) methods are mocked
    # or return dummy data. In a real test, you might want to monkeypatch the
    # llm_client.analyze_thread_structure and llm_client.analyze_arguments methods.
    # For this example, we assume that the LLM returns valid dummy thread data.

    # To simulate a valid LLM response, monkeypatch the analyze_thread_structure method:
    async def dummy_analyze_thread_structure(arguments_data):
        # Return a dummy thread structure matching the expected schema
        # Here we group all argument IDs into one thread with a dummy summary.
        dummy_response = {
            "threads": [
                {
                    "initial_argument_id": 0,
                    "argument_ids": [0, 1, 2],
                    "summary": "Dummy summary for marketing budget discussion."
                }
            ]
        }
        return dummy_response

    # Monkey-patch the method on the LLM client instance
    llm_client.analyze_thread_structure = dummy_analyze_thread_structure

    # Since the analyzer.analyze method expects transcription segments and topics,
    # and then extracts arguments via _extract_arguments, we simulate this by
    # directly calling _build_threads. Alternatively, you can create a wrapper test.
    # Here, we bypass _extract_arguments and directly supply our arguments.
    threads = await analyzer._build_threads(arguments, "Marketing Discussion")

    # Print results for debugging purposes
    print("\n" + "=" * 50)
    print("ARGUMENT ANALYSIS RESULTS")
    print("=" * 50)
    for thread in threads:
        print(f"\nThread Summary: {thread.summary}")
        print("Arguments:")
        for arg in thread.arguments:
            print(f"  - {arg.speaker_id}: {arg.main_claim} ({arg.argument_type})")
    print("=" * 50)

    # Basic assertions
    assert threads is not None
    assert isinstance(threads, list)
    assert len(threads) > 0
    assert all(isinstance(thread, DiscussionThread) for thread in threads)
    # Ensure that each argument in the thread has a thread_id assigned.
    assert all(arg.thread_id is not None for thread in threads for arg in thread.arguments)

    # Clean up
    await llm_client.close()
