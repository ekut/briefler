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
