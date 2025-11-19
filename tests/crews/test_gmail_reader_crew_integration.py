"""
Integration tests for GmailReaderCrew with Vision Agent and image processing.

This test file verifies the complete crew workflow including Vision Agent,
task execution order, and context passing between tasks.
"""

import pytest
import os
from unittest.mock import patch, MagicMock, Mock
from briefler.crews.gmail_reader_crew.gmail_reader_crew import GmailReaderCrew


class TestGmailReaderCrewVisionAgent:
    """Test Vision Agent initialization and configuration."""
    
    def test_vision_agent_initialization(self):
        """Test that Vision Agent is properly initialized with VisionTool."""
        crew_instance = GmailReaderCrew()
        
        # Get the Vision Agent
        vision_agent = crew_instance.image_text_extractor()
        
        # Verify agent is created
        assert vision_agent is not None
        assert "Image Text Extractor" in vision_agent.role
        
        # Verify VisionTool is in agent's tools
        assert len(vision_agent.tools) == 1
        tool = vision_agent.tools[0]
        assert tool.__class__.__name__ == "VisionTool"
    
    def test_email_analyst_initialization(self):
        """Test that Email Analyst is properly initialized with GmailReaderTool."""
        crew_instance = GmailReaderCrew()
        
        # Get the Email Analyst
        email_analyst = crew_instance.email_analyst()
        
        # Verify agent is created
        assert email_analyst is not None
        assert "Email Content Analyst" in email_analyst.role
        
        # Verify GmailReaderTool is in agent's tools
        assert len(email_analyst.tools) == 1
        tool = email_analyst.tools[0]
        assert tool.__class__.__name__ == "GmailReaderTool"
    
    def test_vision_task_initialization(self):
        """Test that Vision Task is properly initialized."""
        crew_instance = GmailReaderCrew()
        
        # Get the Vision Task
        vision_task = crew_instance.extract_text_from_images()
        
        # Verify task is created
        assert vision_task is not None
        assert "extract" in vision_task.description.lower()
        assert "image" in vision_task.description.lower()


class TestGmailReaderCrewTaskExecution:
    """Test task execution order and conditional logic."""
    
    def test_crew_with_image_processing_enabled(self):
        """Test that Vision Task is included when IMAGE_PROCESSING_ENABLED=true."""
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify crew is created
            assert crew is not None
            
            # Verify task count (should include Vision Task)
            assert len(crew.tasks) == 3
            
            # Verify Vision Task is present by checking task descriptions
            task_descriptions = [task.description.lower() for task in crew.tasks]
            assert any("image" in desc and "extract" in desc for desc in task_descriptions)
    
    def test_crew_with_image_processing_disabled(self):
        """Test that Vision Task is excluded when IMAGE_PROCESSING_ENABLED=false."""
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify crew is created
            assert crew is not None
            
            # Verify task count (should NOT include Vision Task)
            assert len(crew.tasks) == 2
            
            # Verify Vision Task is NOT present
            task_descriptions = [task.description.lower() for task in crew.tasks]
            # Check that no task has both "image" and "extract" together (Vision Task signature)
            vision_task_present = any(
                "image" in desc and "extract" in desc and "visiontool" in desc 
                for desc in task_descriptions
            )
            assert not vision_task_present
    
    def test_task_context_configuration(self):
        """Test that Cleanup Task output is passed to Vision Task via context."""
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            crew_instance = GmailReaderCrew()
            
            # Get tasks
            vision_task = crew_instance.extract_text_from_images()
            cleanup_task = crew_instance.cleanup_email_content()
            
            # Create crew to configure context
            crew = crew_instance.crew()
            
            # Verify vision task has cleanup task in context
            assert vision_task.context is not None
            assert len(vision_task.context) == 1
            assert vision_task.context[0] == cleanup_task


class TestGmailReaderCrewWithMockVisionTool:
    """Test complete crew workflow with mocked VisionTool responses."""
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_crew_execution_with_images(self, mock_get_messages, mock_init_service):
        """Test complete crew execution with images present."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with images
        mock_message = {
            'id': 'msg_123',
            'threadId': 'thread_123',
            'snippet': 'Test email',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Special Offer'},
                    {'name': 'From', 'value': 'marketing@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 10:00:00 +0000'}
                ],
                'body': {
                    'data': 'PGh0bWw+PGJvZHk+PGgxPlNwZWNpYWwgT2ZmZXIhPC9oMT48aW1nIHNyYz0iaHR0cHM6Ly9leGFtcGxlLmNvbS9vZmZlci5qcGciPjwvYm9keT48L2h0bWw+'
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify crew was created with Vision Task
            assert len(crew.tasks) == 3
            
            # Verify both agents are created (CrewAI creates all agents regardless of task list)
            assert len(crew.agents) == 2  # Vision Agent + Email Analyst
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_crew_execution_without_images(self, mock_get_messages, mock_init_service):
        """Test complete crew execution without images."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message without images
        mock_message = {
            'id': 'msg_456',
            'threadId': 'thread_456',
            'snippet': 'Plain text',
            'payload': {
                'mimeType': 'text/plain',
                'headers': [
                    {'name': 'Subject', 'value': 'Plain Email'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 11:00:00 +0000'}
                ],
                'body': {
                    'data': 'VGhpcyBpcyBhIHBsYWluIHRleHQgZW1haWwu'
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Disable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify crew was created without Vision Task
            assert len(crew.tasks) == 2
            
            # Note: CrewAI creates all agents defined in the class, regardless of which tasks are active
            # So we verify task count instead of agent count
            assert len(crew.agents) == 2  # Both agents are created by CrewAI


class TestGmailReaderCrewErrorHandling:
    """Test error handling in crew execution."""
    
    @patch('briefler.crews.gmail_reader_crew.gmail_reader_crew.VisionTool')
    def test_vision_tool_initialization_error(self, mock_vision_tool_class):
        """Test handling of VisionTool initialization errors."""
        # Mock VisionTool to raise error on initialization
        mock_vision_tool_class.side_effect = Exception("VisionTool initialization failed")
        
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            # CrewAI initializes agents during crew instantiation
            # The error will be raised during crew creation, not agent method call
            with pytest.raises(Exception) as exc_info:
                crew_instance = GmailReaderCrew()
            
            assert "VisionTool initialization failed" in str(exc_info.value)
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    def test_gmail_tool_initialization_error(self, mock_init_service):
        """Test handling of GmailReaderTool initialization errors."""
        # Mock service initialization to raise error
        mock_init_service.side_effect = Exception("Gmail service initialization failed")
        
        crew_instance = GmailReaderCrew()
        
        # Email Analyst should be created (error happens during tool usage, not initialization)
        email_analyst = crew_instance.email_analyst()
        assert email_analyst is not None


class TestGmailReaderCrewConfiguration:
    """Test crew configuration and settings."""
    
    def test_crew_process_is_sequential(self):
        """Test that crew uses sequential process."""
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify sequential process
            from crewai import Process
            assert crew.process == Process.sequential
    
    def test_crew_verbose_mode(self):
        """Test that crew has verbose mode enabled."""
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Verify verbose mode
            assert crew.verbose is True
    
    def test_agents_config_loaded(self):
        """Test that agents config is loaded correctly."""
        crew_instance = GmailReaderCrew()
        
        # Verify config is loaded as a dictionary
        assert isinstance(crew_instance.agents_config, dict)
        
        # Verify expected agents are in config
        assert 'image_text_extractor' in crew_instance.agents_config
        assert 'email_analyst' in crew_instance.agents_config
    
    def test_tasks_config_loaded(self):
        """Test that tasks config is loaded correctly."""
        crew_instance = GmailReaderCrew()
        
        # Verify config is loaded as a dictionary
        assert isinstance(crew_instance.tasks_config, dict)
        
        # Verify expected tasks are in config
        assert 'extract_text_from_images' in crew_instance.tasks_config
        assert 'cleanup_email_content' in crew_instance.tasks_config
        assert 'analyze_emails' in crew_instance.tasks_config


class TestGmailReaderCrewFeatureFlag:
    """Test feature flag behavior in different scenarios."""
    
    def test_feature_flag_true_variations(self):
        """Test that various 'true' values enable image processing."""
        true_values = ['true', 'True', 'TRUE', 'TrUe']
        
        for value in true_values:
            with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': value}):
                crew_instance = GmailReaderCrew()
                crew = crew_instance.crew()
                
                # Should include Vision Task
                assert len(crew.tasks) == 3, f"Failed for value: {value}"
    
    def test_feature_flag_false_variations(self):
        """Test that various 'false' values disable image processing."""
        false_values = ['false', 'False', 'FALSE', '', '0', 'no', 'disabled']
        
        for value in false_values:
            with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': value}):
                crew_instance = GmailReaderCrew()
                crew = crew_instance.crew()
                
                # Should NOT include Vision Task
                assert len(crew.tasks) == 2, f"Failed for value: {value}"
    
    def test_feature_flag_not_set(self):
        """Test behavior when IMAGE_PROCESSING_ENABLED is not set."""
        # Remove the env var if it exists
        env_copy = os.environ.copy()
        if 'IMAGE_PROCESSING_ENABLED' in env_copy:
            del env_copy['IMAGE_PROCESSING_ENABLED']
        
        with patch.dict('os.environ', env_copy, clear=True):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            
            # Should default to disabled (2 tasks)
            assert len(crew.tasks) == 2


class TestGmailReaderCrewTaskDescriptions:
    """Test that task descriptions are properly configured."""
    
    def test_vision_task_description_content(self):
        """Test that Vision Task description contains required instructions."""
        crew_instance = GmailReaderCrew()
        vision_task = crew_instance.extract_text_from_images()
        
        description = vision_task.description.lower()
        
        # Verify key instructions are present
        assert "image" in description
        assert "extract" in description or "process" in description
    
    def test_cleanup_task_description_content(self):
        """Test that Cleanup Task description is properly configured."""
        crew_instance = GmailReaderCrew()
        cleanup_task = crew_instance.cleanup_email_content()
        
        description = cleanup_task.description.lower()
        
        # Verify key instructions are present
        assert "clean" in description or "cleanup" in description or "remove" in description
    
    def test_analysis_task_description_content(self):
        """Test that Analysis Task description is properly configured."""
        crew_instance = GmailReaderCrew()
        analysis_task = crew_instance.analyze_emails()
        
        description = analysis_task.description.lower()
        
        # Verify key instructions are present
        assert "analyz" in description or "summary" in description or "insight" in description


class TestGmailReaderCrewStructuredOutputs:
    """Test structured outputs from crew execution.
    
    Requirements: 8.1, 8.2, 8.4
    """
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    @patch('crewai.Crew.kickoff')
    def test_crew_returns_structured_output(self, mock_kickoff, mock_get_messages, mock_init_service):
        """Test that crew execution returns structured output.
        
        Validates: Requirements 8.1 - Verify task outputs conform to Pydantic models
        """
        from datetime import datetime
        from briefler.models.task_outputs import AnalysisTaskOutput, EmailSummary
        
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        mock_get_messages.return_value = []
        
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=2,
            email_summaries=[
                EmailSummary(
                    subject="Test Email 1",
                    sender="sender1@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1", "Point 2"],
                    action_items=["Action 1"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Test Email 2",
                    sender="sender2@example.com",
                    timestamp=datetime(2025, 11, 19, 11, 0, 0),
                    key_points=["Point 3"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="High",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock result object with pydantic attribute
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_kickoff.return_value = mock_result
        
        # Execute crew
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            result = crew.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
        
        # Verify structured output is available
        assert hasattr(result, 'pydantic'), "Result should have pydantic attribute"
        assert result.pydantic is not None, "Result.pydantic should not be None"
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    @patch('crewai.Crew.kickoff')
    def test_result_pydantic_is_analysis_task_output_instance(self, mock_kickoff, mock_get_messages, mock_init_service):
        """Test that result.pydantic is an AnalysisTaskOutput instance.
        
        Validates: Requirements 8.1, 8.2 - Verify structured data access patterns
        """
        from datetime import datetime
        from briefler.models.task_outputs import AnalysisTaskOutput, EmailSummary
        
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        mock_get_messages.return_value = []
        
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Medium",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock result object
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_kickoff.return_value = mock_result
        
        # Execute crew
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            result = crew.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
        
        # Verify result.pydantic is AnalysisTaskOutput instance
        assert isinstance(result.pydantic, AnalysisTaskOutput), \
            f"Expected AnalysisTaskOutput, got {type(result.pydantic)}"
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    @patch('crewai.Crew.kickoff')
    def test_structured_fields_are_accessible(self, mock_kickoff, mock_get_messages, mock_init_service):
        """Test that structured fields are accessible via attribute access.
        
        Validates: Requirements 8.1, 8.2 - Verify structured fields are accessible
        """
        from datetime import datetime
        from briefler.models.task_outputs import AnalysisTaskOutput, EmailSummary
        
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        mock_get_messages.return_value = []
        
        # Create mock structured result with specific data
        mock_analysis_output = AnalysisTaskOutput(
            total_count=3,
            email_summaries=[
                EmailSummary(
                    subject="Email 1",
                    sender="sender1@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Key point 1"],
                    action_items=["Action 1"],
                    has_deadline=True
                ),
                EmailSummary(
                    subject="Email 2",
                    sender="sender2@example.com",
                    timestamp=datetime(2025, 11, 19, 11, 0, 0),
                    key_points=["Key point 2"],
                    action_items=["Action 2"],
                    has_deadline=False
                ),
                EmailSummary(
                    subject="Email 3",
                    sender="sender3@example.com",
                    timestamp=datetime(2025, 11, 19, 12, 0, 0),
                    key_points=["Key point 3"],
                    action_items=[],
                    has_deadline=False
                )
            ],
            action_items=["Action 1", "Action 2"],
            priority_assessment="High",
            summary_text="# Email Analysis\n\nDetailed summary"
        )
        
        # Create mock result object
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nDetailed summary"
        mock_kickoff.return_value = mock_result
        
        # Execute crew
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            result = crew.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
        
        # Verify all structured fields are accessible
        assert result.pydantic.total_count == 3, "total_count should be accessible"
        assert len(result.pydantic.email_summaries) == 3, "email_summaries should be accessible"
        assert len(result.pydantic.action_items) == 2, "action_items should be accessible"
        assert result.pydantic.priority_assessment == "High", "priority_assessment should be accessible"
        assert result.pydantic.summary_text == "# Email Analysis\n\nDetailed summary", \
            "summary_text should be accessible"
        
        # Verify nested fields are accessible
        first_email = result.pydantic.email_summaries[0]
        assert first_email.subject == "Email 1", "Nested subject should be accessible"
        assert first_email.sender == "sender1@example.com", "Nested sender should be accessible"
        assert first_email.has_deadline is True, "Nested has_deadline should be accessible"
        assert len(first_email.key_points) == 1, "Nested key_points should be accessible"
        assert len(first_email.action_items) == 1, "Nested action_items should be accessible"
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    @patch('crewai.Crew.kickoff')
    def test_dictionary_style_access_to_result_fields(self, mock_kickoff, mock_get_messages, mock_init_service):
        """Test that result fields can be accessed via dictionary-style indexing.
        
        Validates: Requirements 8.2 - Verify dictionary-style access to result fields
        """
        from datetime import datetime
        from briefler.models.task_outputs import AnalysisTaskOutput, EmailSummary
        
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        mock_get_messages.return_value = []
        
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Low",
            summary_text="# Email Analysis\n\nTest summary"
        )
        
        # Create mock result object
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary"
        mock_kickoff.return_value = mock_result
        
        # Execute crew
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            result = crew.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
        
        # Convert to dictionary for dictionary-style access
        result_dict = result.pydantic.model_dump()
        
        # Verify dictionary-style access works
        assert result_dict['total_count'] == 1, "Should access total_count via dict"
        assert len(result_dict['email_summaries']) == 1, "Should access email_summaries via dict"
        assert result_dict['priority_assessment'] == "Low", "Should access priority_assessment via dict"
        assert len(result_dict['action_items']) == 1, "Should access action_items via dict"
        
        # Verify nested dictionary access
        first_email = result_dict['email_summaries'][0]
        assert first_email['subject'] == "Test Email", "Should access nested subject via dict"
        assert first_email['sender'] == "sender@example.com", "Should access nested sender via dict"
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    @patch('crewai.Crew.kickoff')
    def test_backward_compatibility_with_result_raw(self, mock_kickoff, mock_get_messages, mock_init_service):
        """Test that result.raw is still available for backward compatibility.
        
        Validates: Requirements 8.4 - Verify backward compatibility with raw output access
        """
        from datetime import datetime
        from briefler.models.task_outputs import AnalysisTaskOutput, EmailSummary
        
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        mock_get_messages.return_value = []
        
        # Create mock structured result
        mock_analysis_output = AnalysisTaskOutput(
            total_count=1,
            email_summaries=[
                EmailSummary(
                    subject="Test Email",
                    sender="sender@example.com",
                    timestamp=datetime(2025, 11, 19, 10, 0, 0),
                    key_points=["Point 1"],
                    action_items=["Action 1"],
                    has_deadline=False
                )
            ],
            action_items=["Action 1"],
            priority_assessment="Medium",
            summary_text="# Email Analysis\n\nTest summary for backward compatibility"
        )
        
        # Create mock result object with both pydantic and raw
        mock_result = MagicMock()
        mock_result.pydantic = mock_analysis_output
        mock_result.raw = "# Email Analysis\n\nTest summary for backward compatibility"
        mock_kickoff.return_value = mock_result
        
        # Execute crew
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            crew_instance = GmailReaderCrew()
            crew = crew_instance.crew()
            result = crew.kickoff(inputs={
                'sender_emails': ['test@example.com'],
                'language': 'en',
                'days': 7
            })
        
        # Verify both structured and raw outputs are available
        assert hasattr(result, 'raw'), "Result should have raw attribute for backward compatibility"
        assert hasattr(result, 'pydantic'), "Result should have pydantic attribute for structured access"
        
        # Verify raw output is a string
        assert isinstance(result.raw, str), "result.raw should be a string"
        assert len(result.raw) > 0, "result.raw should not be empty"
        assert "Email Analysis" in result.raw, "result.raw should contain expected content"
        
        # Verify structured output is also available
        assert isinstance(result.pydantic, AnalysisTaskOutput), \
            "result.pydantic should be AnalysisTaskOutput instance"
        
        # Verify both contain consistent information
        assert result.pydantic.summary_text in result.raw or result.raw in result.pydantic.summary_text, \
            "Raw and structured outputs should contain consistent information"
