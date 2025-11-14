"""
Integration tests for GmailReaderTool with image extraction feature.

This test file verifies the integration between GmailReaderTool and ImageExtractor,
testing the complete workflow with feature flag enabled/disabled.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock, Mock
from briefler.tools.gmail_reader_tool import GmailReaderTool


class TestGmailReaderToolImageExtraction:
    """Test GmailReaderTool with image extraction feature."""
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_extract_images_with_feature_enabled(self, mock_get_messages, mock_init_service, caplog):
        """Test that images are extracted when IMAGE_PROCESSING_ENABLED=true."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with HTML containing images
        mock_message = {
            'id': 'msg_123',
            'threadId': 'thread_123',
            'snippet': 'Test email with images',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Marketing Email'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 10:00:00 +0000'}
                ],
                'body': {
                    'data': 'PGh0bWw+PGJvZHk+PGgxPlNwZWNpYWwgT2ZmZXIhPC9oMT48aW1nIHNyYz0iaHR0cHM6Ly9leGFtcGxlLmNvbS9pbWFnZTEuanBnIj48aW1nIHNyYz0iaHR0cHM6Ly9leGFtcGxlLmNvbS9pbWFnZTIucG5nIj48L2JvZHk+PC9odG1sPg=='
                    # Decodes to: <html><body><h1>Special Offer!</h1><img src="https://example.com/image1.jpg"><img src="https://example.com/image2.png"></body></html>
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.INFO):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify images were extracted
        assert 'IMAGES_FOR_PROCESSING: 2' in result
        assert 'IMAGE_1: https://example.com/image1.jpg' in result
        assert 'IMAGE_2: https://example.com/image2.png' in result
        
        # Verify logging
        assert "Found 2 image(s) in message msg_123" in caplog.text
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_no_image_extraction_with_feature_disabled(self, mock_get_messages, mock_init_service, caplog):
        """Test that images are NOT extracted when IMAGE_PROCESSING_ENABLED=false."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with HTML containing images
        mock_message = {
            'id': 'msg_456',
            'threadId': 'thread_456',
            'snippet': 'Test email with images',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Newsletter'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 11:00:00 +0000'}
                ],
                'body': {
                    'data': 'PGh0bWw+PGJvZHk+PGltZyBzcmM9Imh0dHBzOi8vZXhhbXBsZS5jb20vaW1hZ2UuanBnIj48L2JvZHk+PC9odG1sPg=='
                    # Decodes to: <html><body><img src="https://example.com/image.jpg"></body></html>
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Disable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'false'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.WARNING):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify images were NOT extracted
        assert 'IMAGES_FOR_PROCESSING' not in result
        assert 'IMAGE_1' not in result
        
        # Verify warning was logged
        assert "Image processing is disabled but message msg_456 contains images" in caplog.text
        assert "Set IMAGE_PROCESSING_ENABLED=true" in caplog.text
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_email_without_images(self, mock_get_messages, mock_init_service, caplog):
        """Test processing email without images (feature enabled)."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with plain text (no images)
        mock_message = {
            'id': 'msg_789',
            'threadId': 'thread_789',
            'snippet': 'Plain text email',
            'payload': {
                'mimeType': 'text/plain',
                'headers': [
                    {'name': 'Subject', 'value': 'Text Only'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 12:00:00 +0000'}
                ],
                'body': {
                    'data': 'VGhpcyBpcyBhIHBsYWluIHRleHQgZW1haWwgd2l0aCBubyBpbWFnZXMu'
                    # Decodes to: This is a plain text email with no images.
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.DEBUG):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify no image section in output
        assert 'IMAGES_FOR_PROCESSING' not in result
        assert 'This is a plain text email with no images.' in result
        
        # Verify logging
        assert "No HTML content found for image extraction" in caplog.text
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_image_extraction_error_handling(self, mock_get_messages, mock_init_service, caplog):
        """Test that image extraction errors don't break email processing."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with HTML
        mock_message = {
            'id': 'msg_error_123',
            'threadId': 'thread_error_123',
            'snippet': 'Test email',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 13:00:00 +0000'}
                ],
                'body': {
                    'data': 'PGh0bWw+PGJvZHk+VGVzdDwvYm9keT48L2h0bWw+'
                    # Decodes to: <html><body>Test</body></html>
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing and mock ImageExtractor to raise error
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            with patch('briefler.tools.gmail_reader_tool.ImageExtractor') as mock_extractor_class:
                mock_extractor = MagicMock()
                mock_extractor.extract_images_from_html.side_effect = Exception("Extraction failed")
                mock_extractor_class.return_value = mock_extractor
                
                tool = GmailReaderTool()
                
                with caplog.at_level(logging.ERROR):
                    result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify email processing continued despite error
        assert 'Test Subject' in result
        assert 'sender@example.com' in result
        
        # Verify error was logged
        assert "Image extraction failed for message msg_error_123" in caplog.text
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_multiple_emails_with_mixed_image_content(self, mock_get_messages, mock_init_service, caplog):
        """Test processing multiple emails with different image content."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create multiple mock messages
        mock_messages = [
            {
                'id': 'msg_1',
                'threadId': 'thread_1',
                'snippet': 'Email with images',
                'payload': {
                    'mimeType': 'text/html',
                    'headers': [
                        {'name': 'Subject', 'value': 'Email 1'},
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'Date', 'value': 'Mon, 13 Nov 2025 10:00:00 +0000'}
                    ],
                    'body': {
                        'data': 'PGh0bWw+PGltZyBzcmM9Imh0dHBzOi8vZXhhbXBsZS5jb20vaW1hZ2UxLmpwZyI+PC9odG1sPg=='
                    }
                }
            },
            {
                'id': 'msg_2',
                'threadId': 'thread_2',
                'snippet': 'Plain text email',
                'payload': {
                    'mimeType': 'text/plain',
                    'headers': [
                        {'name': 'Subject', 'value': 'Email 2'},
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'Date', 'value': 'Mon, 13 Nov 2025 11:00:00 +0000'}
                    ],
                    'body': {
                        'data': 'UGxhaW4gdGV4dA=='
                    }
                }
            },
            {
                'id': 'msg_3',
                'threadId': 'thread_3',
                'snippet': 'Email with multiple images',
                'payload': {
                    'mimeType': 'text/html',
                    'headers': [
                        {'name': 'Subject', 'value': 'Email 3'},
                        {'name': 'From', 'value': 'sender@example.com'},
                        {'name': 'Date', 'value': 'Mon, 13 Nov 2025 12:00:00 +0000'}
                    ],
                    'body': {
                        'data': 'PGh0bWw+PGltZyBzcmM9Imh0dHBzOi8vZXhhbXBsZS5jb20vaW1hZ2UyLmpwZyI+PGltZyBzcmM9Imh0dHBzOi8vZXhhbXBsZS5jb20vaW1hZ2UzLnBuZyI+PC9odG1sPg=='
                    }
                }
            }
        ]
        mock_get_messages.return_value = mock_messages
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.INFO):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify all emails were processed
        assert 'Email 1' in result
        assert 'Email 2' in result
        assert 'Email 3' in result
        
        # Verify image extraction for emails with images
        assert 'IMAGES_FOR_PROCESSING: 1' in result  # Email 1
        assert 'IMAGES_FOR_PROCESSING: 2' in result  # Email 3
        
        # Count occurrences of IMAGES_FOR_PROCESSING (should be 2 - for msg_1 and msg_3)
        image_sections = result.count('IMAGES_FOR_PROCESSING')
        assert image_sections == 2
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_multipart_email_with_images(self, mock_get_messages, mock_init_service, caplog):
        """Test processing multipart email with images in HTML part."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock multipart message
        mock_message = {
            'id': 'msg_multipart_123',
            'threadId': 'thread_multipart_123',
            'snippet': 'Multipart email',
            'payload': {
                'mimeType': 'multipart/alternative',
                'headers': [
                    {'name': 'Subject', 'value': 'Multipart Email'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 14:00:00 +0000'}
                ],
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {
                            'data': 'UGxhaW4gdGV4dCB2ZXJzaW9u'
                        }
                    },
                    {
                        'mimeType': 'text/html',
                        'body': {
                            'data': 'PGh0bWw+PGJvZHk+PGltZyBzcmM9Imh0dHBzOi8vZXhhbXBsZS5jb20vbXVsdGlwYXJ0LmpwZyI+PC9ib2R5PjwvaHRtbD4='
                        }
                    }
                ]
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.INFO):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify images were extracted from HTML part
        assert 'IMAGES_FOR_PROCESSING: 1' in result
        assert 'IMAGE_1: https://example.com/multipart.jpg' in result
        
        # Verify logging
        assert "Found 1 image(s) in message msg_multipart_123" in caplog.text


class TestGmailReaderToolImageExtractionEdgeCases:
    """Test edge cases for image extraction in GmailReaderTool."""
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_html_extraction_error_handling(self, mock_get_messages, mock_init_service, caplog):
        """Test that HTML extraction errors are handled gracefully."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with malformed payload
        mock_message = {
            'id': 'msg_malformed_123',
            'threadId': 'thread_malformed_123',
            'snippet': 'Test',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Test'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 15:00:00 +0000'}
                ],
                'body': {
                    'data': 'invalid_base64!!!'
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.ERROR):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify email processing continued
        assert 'Test' in result
        assert 'sender@example.com' in result
        
        # No images should be extracted due to decoding error
        assert 'IMAGES_FOR_PROCESSING' not in result
    
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._initialize_gmail_service')
    @patch('briefler.tools.gmail_reader_tool.GmailReaderTool._get_unread_messages')
    def test_empty_html_content(self, mock_get_messages, mock_init_service, caplog):
        """Test handling of empty HTML content."""
        # Mock Gmail service
        mock_service = MagicMock()
        mock_init_service.return_value = mock_service
        
        # Create mock message with empty body
        mock_message = {
            'id': 'msg_empty_123',
            'threadId': 'thread_empty_123',
            'snippet': 'Empty',
            'payload': {
                'mimeType': 'text/html',
                'headers': [
                    {'name': 'Subject', 'value': 'Empty Email'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'Date', 'value': 'Mon, 13 Nov 2025 16:00:00 +0000'}
                ],
                'body': {
                    'data': ''
                }
            }
        }
        mock_get_messages.return_value = [mock_message]
        
        # Enable image processing
        with patch.dict('os.environ', {'IMAGE_PROCESSING_ENABLED': 'true'}):
            tool = GmailReaderTool()
            
            with caplog.at_level(logging.DEBUG):
                result = tool._run(sender_emails=['sender@example.com'], days=7)
        
        # Verify no images extracted
        assert 'IMAGES_FOR_PROCESSING' not in result
        
        # Verify logging
        assert "No HTML content found for image extraction" in caplog.text
