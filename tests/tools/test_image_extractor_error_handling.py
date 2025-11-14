"""
Tests for Image Extractor error handling and logging.

This test file verifies that the Image Extractor properly handles errors
and logs appropriate messages during image extraction.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from briefler.tools.image_extractor import ImageExtractor, ImageReference


class TestImageExtractorErrorHandling:
    """Test error handling in ImageExtractor."""
    
    def test_extract_images_with_empty_html(self, caplog):
        """Test that empty HTML is handled gracefully."""
        extractor = ImageExtractor()
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html("", "test_msg_123")
        
        assert result == []
        assert "No HTML content provided" in caplog.text
    
    def test_extract_images_with_malformed_html(self, caplog):
        """Test that malformed HTML doesn't crash the extractor."""
        extractor = ImageExtractor()
        # HTML with unclosed tags but valid img tag
        html = "<div><img src='https://example.com/image.jpg'><p>unclosed"
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html(html, "test_msg_123")
        
        # Should still extract the image despite malformed HTML
        assert len(result) == 1
        assert result[0].external_url == "https://example.com/image.jpg"
    
    def test_extract_images_skips_non_https(self, caplog):
        """Test that non-HTTPS images are skipped and logged."""
        extractor = ImageExtractor()
        html = """
        <img src="http://example.com/image1.jpg">
        <img src="https://example.com/image2.jpg">
        """
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html(html, "test_msg_123")
        
        assert len(result) == 1
        assert result[0].external_url == "https://example.com/image2.jpg"
        assert "Skipping non-HTTPS image" in caplog.text
        assert "skipped: 1 non-HTTPS" in caplog.text
    
    def test_extract_images_logs_summary(self, caplog):
        """Test that extraction logs a summary of results."""
        extractor = ImageExtractor()
        html = """
        <img src="https://example.com/image1.jpg">
        <img src="http://example.com/image2.jpg">
        <img src="https://example.com/image3.jpg">
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "test_msg_123")
        
        assert len(result) == 2
        assert "Extracted 2 external image(s)" in caplog.text
        assert "skipped: 1 non-HTTPS, 0 invalid" in caplog.text
    
    def test_validate_url_with_invalid_scheme(self, caplog):
        """Test URL validation with non-HTTPS scheme."""
        extractor = ImageExtractor()
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.validate_external_url("http://example.com/image.jpg")
        
        assert result is False
        assert "non-HTTPS scheme" in caplog.text
    
    def test_validate_url_with_missing_domain(self, caplog):
        """Test URL validation with missing domain."""
        extractor = ImageExtractor()
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.validate_external_url("https://")
        
        assert result is False
        assert "missing domain" in caplog.text
    
    def test_validate_url_with_whitelist(self, caplog):
        """Test URL validation with domain whitelist."""
        with patch.dict('os.environ', {'IMAGE_ALLOWED_DOMAINS': 'example.com,trusted.com'}):
            extractor = ImageExtractor()
            
            with caplog.at_level(logging.DEBUG):
                # Should pass - domain in whitelist
                result1 = extractor.validate_external_url("https://example.com/image.jpg")
                assert result1 is True
                
                # Should fail - domain not in whitelist
                result2 = extractor.validate_external_url("https://untrusted.com/image.jpg")
                assert result2 is False
                assert "Domain not in whitelist" in caplog.text
    
    def test_extract_images_handles_regex_error(self, caplog):
        """Test that regex errors are handled gracefully."""
        extractor = ImageExtractor()
        
        # Mock re.findall to raise an error
        with patch('briefler.tools.image_extractor.re.findall', side_effect=Exception("Regex error")):
            with caplog.at_level(logging.ERROR):
                result = extractor.extract_images_from_html("<img src='test'>", "test_msg_123")
        
        assert result == []
        assert "Failed to extract images from HTML" in caplog.text
    
    def test_extract_images_continues_on_individual_error(self, caplog):
        """Test that extraction continues even if one image fails."""
        extractor = ImageExtractor()
        html = """
        <img src="https://example.com/image1.jpg">
        <img src="https://example.com/image2.jpg">
        """
        
        # Mock ImageReference to fail on first call, succeed on second
        call_count = 0
        original_init = ImageReference.__init__
        
        def mock_init(self, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Test error")
            original_init(self, **kwargs)
        
        with patch.object(ImageReference, '__init__', mock_init):
            with caplog.at_level(logging.ERROR):
                result = extractor.extract_images_from_html(html, "test_msg_123")
        
        # Should still extract the second image
        assert len(result) == 1
        assert "Failed to create ImageReference" in caplog.text


class TestImageExtractorLogging:
    """Test logging behavior in ImageExtractor."""
    
    def test_logs_images_found(self, caplog):
        """Test that found images are logged."""
        extractor = ImageExtractor()
        html = '<img src="https://example.com/image.jpg">'
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html(html, "test_msg_123")
        
        assert len(result) == 1
        assert "Found 1 <img> tag(s)" in caplog.text
        assert "Validated image 1" in caplog.text
    
    def test_logs_no_images_found(self, caplog):
        """Test logging when no valid images are found."""
        extractor = ImageExtractor()
        html = '<img src="http://example.com/image.jpg">'  # Non-HTTPS
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html(html, "test_msg_123")
        
        assert len(result) == 0
        assert "No valid external images found" in caplog.text
    
    def test_logs_whitelist_configuration(self, caplog):
        """Test that whitelist configuration is logged."""
        with patch.dict('os.environ', {'IMAGE_ALLOWED_DOMAINS': 'example.com,trusted.com'}):
            with caplog.at_level(logging.INFO):
                extractor = ImageExtractor()
        
        assert "Image domain whitelist enabled: 2 domains configured" in caplog.text
