"""
Integration tests for Image Extractor with sample HTML containing external URLs.

This test file verifies the complete image extraction workflow with realistic
HTML email content containing external HTTPS URLs.
"""

import pytest
import logging
from unittest.mock import patch
from briefler.tools.image_extractor import ImageExtractor, ImageReference


class TestImageExtractorIntegration:
    """Integration tests for ImageExtractor with realistic HTML samples."""
    
    def test_extract_from_marketing_email_html(self, caplog):
        """Test extraction from realistic marketing email HTML with multiple images."""
        extractor = ImageExtractor()
        
        # Realistic marketing email HTML with external URLs
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Special Offer</title></head>
        <body>
            <div style="max-width: 600px;">
                <img src="https://cdn.example.com/newsletter/header-banner.jpg" alt="Header" width="600">
                <p>Check out our latest offers!</p>
                <img src="https://images.example.com/products/special-deal.png" alt="Deal" width="300">
                <p>Limited time only!</p>
                <img src="https://static.example.com/footer-logo.gif" alt="Logo" width="150">
            </div>
        </body>
        </html>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_marketing_123")
        
        # Should extract all 3 HTTPS images
        assert len(result) == 3
        
        # Verify image references are correctly structured
        assert result[0].message_id == "msg_marketing_123"
        assert result[0].image_index == 1
        assert result[0].external_url == "https://cdn.example.com/newsletter/header-banner.jpg"
        
        assert result[1].image_index == 2
        assert result[1].external_url == "https://images.example.com/products/special-deal.png"
        
        assert result[2].image_index == 3
        assert result[2].external_url == "https://static.example.com/footer-logo.gif"
        
        # Verify logging
        assert "Extracted 3 external image(s)" in caplog.text
    
    def test_extract_from_gmail_proxied_urls(self, caplog):
        """Test extraction from Gmail-proxied image URLs (common in real emails)."""
        extractor = ImageExtractor()
        
        # Gmail often proxies external images through googleusercontent.com
        html = """
        <div>
            <img src="https://ci3.googleusercontent.com/meips/ADKq_NZxyz123=s0-d-e1-ft#https://image.info.example.com/banner.jpg">
            <img src="https://ci4.googleusercontent.com/meips/ADKq_NZabc456=s0-d-e1-ft#https://cdn.example.com/promo.png">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_gmail_proxy_123")
        
        # Should extract both proxied URLs
        assert len(result) == 2
        assert "googleusercontent.com" in result[0].external_url
        assert "googleusercontent.com" in result[1].external_url
        
        # Verify sequential indexing
        assert result[0].image_index == 1
        assert result[1].image_index == 2
    
    def test_extract_mixed_http_https_urls(self, caplog):
        """Test that HTTP URLs are skipped while HTTPS URLs are extracted."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src="http://insecure.example.com/image1.jpg">
            <img src="https://secure.example.com/image2.jpg">
            <img src="http://another-insecure.com/image3.png">
            <img src="https://another-secure.com/image4.png">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_mixed_123")
        
        # Should only extract HTTPS URLs
        assert len(result) == 2
        assert all("https://" in ref.external_url for ref in result)
        assert "secure.example.com" in result[0].external_url
        assert "another-secure.com" in result[1].external_url
        
        # Verify skipped count in logs
        assert "skipped: 2 non-HTTPS" in caplog.text
    
    def test_extract_with_domain_whitelist(self, caplog):
        """Test extraction with domain whitelist configuration."""
        with patch.dict('os.environ', {'IMAGE_ALLOWED_DOMAINS': 'trusted.com,cdn.example.com'}):
            with caplog.at_level(logging.INFO):
                extractor = ImageExtractor()
                
                html = """
                <div>
                    <img src="https://trusted.com/image1.jpg">
                    <img src="https://untrusted.com/image2.jpg">
                    <img src="https://cdn.example.com/image3.png">
                    <img src="https://another-untrusted.com/image4.jpg">
                </div>
                """
                
                result = extractor.extract_images_from_html(html, "msg_whitelist_123")
            
            # Should only extract from whitelisted domains
            assert len(result) == 2
            assert "trusted.com" in result[0].external_url
            assert "cdn.example.com" in result[1].external_url
            
            # Verify whitelist configuration was logged
            assert "Image domain whitelist enabled: 2 domains configured" in caplog.text
            assert "skipped: 0 non-HTTPS, 2 invalid" in caplog.text
    
    def test_extract_from_complex_nested_html(self, caplog):
        """Test extraction from complex nested HTML structure."""
        extractor = ImageExtractor()
        
        html = """
        <html>
        <body>
            <table>
                <tr>
                    <td>
                        <div style="background: #fff;">
                            <img src="https://example.com/nested1.jpg" style="display:block;">
                        </div>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><img src="https://example.com/nested2.png"></td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            <div>
                <span><img src="https://example.com/nested3.gif"></span>
            </div>
        </body>
        </html>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_nested_123")
        
        # Should extract all images regardless of nesting
        assert len(result) == 3
        assert all(ref.message_id == "msg_nested_123" for ref in result)
        assert result[0].image_index == 1
        assert result[1].image_index == 2
        assert result[2].image_index == 3
    
    def test_extract_with_query_parameters(self, caplog):
        """Test extraction of URLs with query parameters (common in tracking pixels)."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src="https://track.example.com/pixel.gif?id=12345&campaign=summer">
            <img src="https://cdn.example.com/image.jpg?size=large&format=webp">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_query_123")
        
        # Should extract URLs with query parameters intact
        assert len(result) == 2
        assert "?id=12345&campaign=summer" in result[0].external_url
        assert "?size=large&format=webp" in result[1].external_url
    
    def test_extract_from_email_with_no_images(self, caplog):
        """Test extraction from HTML email with no images."""
        extractor = ImageExtractor()
        
        html = """
        <html>
        <body>
            <h1>Important Notice</h1>
            <p>This is a text-only email with no images.</p>
            <p>Please read carefully.</p>
        </body>
        </html>
        """
        
        with caplog.at_level(logging.DEBUG):
            result = extractor.extract_images_from_html(html, "msg_no_images_123")
        
        # Should return empty list
        assert result == []
        assert "No valid external images found" in caplog.text
    
    def test_extract_with_single_quotes_in_src(self, caplog):
        """Test extraction with single quotes in src attribute."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src='https://example.com/single-quote.jpg'>
            <img src="https://example.com/double-quote.jpg">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_quotes_123")
        
        # Should handle both single and double quotes
        assert len(result) == 2
        assert "single-quote.jpg" in result[0].external_url
        assert "double-quote.jpg" in result[1].external_url
    
    def test_extract_preserves_url_encoding(self, caplog):
        """Test that URL encoding is preserved in extracted URLs."""
        extractor = ImageExtractor()
        
        html = """
        <img src="https://example.com/path%20with%20spaces/image.jpg">
        <img src="https://example.com/special%2Bchars%3Dvalue.png">
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_encoding_123")
        
        # Should preserve URL encoding
        assert len(result) == 2
        assert "%20" in result[0].external_url
        assert "%2B" in result[1].external_url
        assert "%3D" in result[1].external_url


class TestImageExtractorEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_extract_with_very_long_url(self, caplog):
        """Test extraction with very long URL (common in tracking/analytics)."""
        extractor = ImageExtractor()
        
        # Create a very long URL (500+ characters)
        long_url = "https://analytics.example.com/track.gif?" + "&".join([f"param{i}=value{i}" for i in range(50)])
        html = f'<img src="{long_url}">'
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_long_url_123")
        
        # Should handle long URLs
        assert len(result) == 1
        assert result[0].external_url == long_url
    
    def test_extract_with_data_uri_scheme(self, caplog):
        """Test that data: URI scheme images are skipped (base64 inline)."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA">
            <img src="https://example.com/real-image.jpg">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_data_uri_123")
        
        # Should skip data: URIs and only extract HTTPS
        assert len(result) == 1
        assert "example.com" in result[0].external_url
    
    def test_extract_with_relative_urls(self, caplog):
        """Test that relative URLs are skipped."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src="/images/logo.png">
            <img src="../assets/banner.jpg">
            <img src="https://example.com/absolute.jpg">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_relative_123")
        
        # Should only extract absolute HTTPS URLs
        assert len(result) == 1
        assert "example.com" in result[0].external_url
    
    def test_extract_with_empty_src_attribute(self, caplog):
        """Test handling of empty src attributes."""
        extractor = ImageExtractor()
        
        html = """
        <div>
            <img src="">
            <img src="https://example.com/valid.jpg">
            <img src="   ">
        </div>
        """
        
        with caplog.at_level(logging.INFO):
            result = extractor.extract_images_from_html(html, "msg_empty_src_123")
        
        # Should skip empty src and only extract valid URL
        assert len(result) == 1
        assert "example.com" in result[0].external_url
