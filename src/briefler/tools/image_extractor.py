"""
Image Extractor Module

Extracts external image URLs from HTML email content for text extraction.
MVP: Focuses on external HTTPS URLs only (no Gmail attachments or base64 inline images).
"""

import logging
import os
import re
from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class ImageReference(BaseModel):
    """Reference to an external image in email content (MVP: External URLs only)."""
    
    message_id: str = Field(..., description="Gmail message ID")
    image_index: int = Field(..., description="Sequential index (1, 2, 3...) for identification")
    external_url: str = Field(..., description="HTTPS URL to the image")


class ImageExtractor:
    """
    Extracts external image URLs from HTML email content.
    
    MVP Scope: External HTTPS URLs only
    - Covers ~95% of promotional/marketing emails
    - No downloading or file management required
    - Direct URL passing to VisionTool
    """
    
    def __init__(self):
        """Initialize ImageExtractor with optional domain whitelist from environment."""
        self.allowed_domains = self._load_allowed_domains()
        
    def _load_allowed_domains(self) -> Optional[List[str]]:
        """
        Load allowed domains from IMAGE_ALLOWED_DOMAINS environment variable.
        
        Returns:
            List of allowed domains if configured, None otherwise (allow all HTTPS)
        """
        domains_str = os.getenv('IMAGE_ALLOWED_DOMAINS', '').strip()
        if not domains_str:
            return None
        
        domains = [d.strip().lower() for d in domains_str.split(',') if d.strip()]
        if domains:
            logger.info(f"Image domain whitelist enabled: {len(domains)} domains configured")
            return domains
        return None
    
    def extract_images_from_html(self, html_content: str, message_id: str) -> List[ImageReference]:
        """
        Parse HTML to identify external image URLs (MVP: External URLs only).
        
        Process:
        1. Parse HTML to find <img> tags
        2. Extract src attributes
        3. Filter for HTTPS URLs only
        4. Validate URLs (format, optional domain whitelist)
        5. Create ImageReference objects with sequential indexing
        
        Args:
            html_content: HTML email content
            message_id: Gmail message ID for context
            
        Returns:
            List of ImageReference objects with external URLs
        """
        if not html_content:
            logger.debug(f"No HTML content provided for message {message_id}")
            return []
        
        try:
            # Find all <img> tags with src attributes using regex
            # Pattern matches: <img ... src="..." ...> or <img ... src='...' ...>
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            
            try:
                matches = re.findall(img_pattern, html_content, re.IGNORECASE)
                logger.debug(f"Found {len(matches)} <img> tag(s) in message {message_id}")
            except re.error as e:
                logger.error(
                    f"Regex pattern error while parsing HTML for message {message_id}",
                    extra={"message_id": message_id, "error": str(e)},
                    exc_info=True
                )
                return []
            
            image_refs = []
            image_index = 1
            skipped_non_https = 0
            skipped_invalid = 0
            
            for src in matches:
                src = src.strip()
                
                # Only process external HTTPS URLs
                if not src.startswith('https://'):
                    skipped_non_https += 1
                    logger.debug(
                        f"Skipping non-HTTPS image in message {message_id}: {src[:50]}...",
                        extra={"message_id": message_id, "image_url": src[:100], "reason": "non-https"}
                    )
                    continue
                
                # Validate URL
                if not self.validate_external_url(src):
                    skipped_invalid += 1
                    logger.debug(
                        f"Skipping invalid/disallowed URL in message {message_id}: {src[:50]}...",
                        extra={"message_id": message_id, "image_url": src[:100], "reason": "validation-failed"}
                    )
                    continue
                
                # Create ImageReference
                try:
                    image_ref = ImageReference(
                        message_id=message_id,
                        image_index=image_index,
                        external_url=src
                    )
                    image_refs.append(image_ref)
                    logger.debug(
                        f"Validated image {image_index} for message {message_id}: {src[:50]}...",
                        extra={"message_id": message_id, "image_index": image_index, "image_url": src[:100]}
                    )
                    image_index += 1
                except Exception as e:
                    logger.error(
                        f"Failed to create ImageReference for message {message_id}",
                        extra={"message_id": message_id, "image_url": src[:100], "error": str(e)},
                        exc_info=True
                    )
                    continue
            
            # Log summary of extraction results
            if image_refs:
                logger.info(
                    f"Extracted {len(image_refs)} external image(s) from message {message_id} "
                    f"(skipped: {skipped_non_https} non-HTTPS, {skipped_invalid} invalid)",
                    extra={
                        "message_id": message_id,
                        "images_found": len(image_refs),
                        "skipped_non_https": skipped_non_https,
                        "skipped_invalid": skipped_invalid
                    }
                )
            else:
                logger.debug(
                    f"No valid external images found in message {message_id} "
                    f"(skipped: {skipped_non_https} non-HTTPS, {skipped_invalid} invalid)",
                    extra={
                        "message_id": message_id,
                        "images_found": 0,
                        "skipped_non_https": skipped_non_https,
                        "skipped_invalid": skipped_invalid
                    }
                )
            
            return image_refs
            
        except Exception as e:
            logger.error(
                f"Failed to extract images from HTML for message {message_id}: {str(e)}",
                extra={"message_id": message_id, "error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            return []
    
    def validate_external_url(self, url: str) -> bool:
        """
        Validate external URL for security and format.
        
        Validation rules:
        1. Must use HTTPS protocol (reject HTTP)
        2. Must be a valid URL format
        3. If IMAGE_ALLOWED_DOMAINS is set, check domain whitelist
        4. If whitelist not set, allow all HTTPS URLs
        
        Args:
            url: Image URL to validate
            
        Returns:
            True if URL is valid and allowed, False otherwise
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            
            # Must be HTTPS
            if parsed.scheme != 'https':
                logger.debug(
                    f"URL validation failed: non-HTTPS scheme '{parsed.scheme}'",
                    extra={"url": url[:100], "scheme": parsed.scheme, "reason": "non-https"}
                )
                return False
            
            # Must have a valid netloc (domain)
            if not parsed.netloc:
                logger.debug(
                    f"URL validation failed: missing domain",
                    extra={"url": url[:100], "reason": "no-domain"}
                )
                return False
            
            # Check domain whitelist if configured
            if self.allowed_domains is not None:
                domain = self.get_domain_from_url(url)
                if domain is None:
                    logger.debug(
                        f"URL validation failed: could not extract domain",
                        extra={"url": url[:100], "reason": "domain-extraction-failed"}
                    )
                    return False
                
                # Check if domain is in whitelist
                if domain.lower() not in self.allowed_domains:
                    logger.debug(
                        f"Domain not in whitelist: {domain}",
                        extra={"url": url[:100], "domain": domain, "reason": "domain-not-whitelisted"}
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(
                f"URL validation exception for {url[:50]}...: {str(e)}",
                extra={"url": url[:100], "error": str(e), "error_type": type(e).__name__},
                exc_info=True
            )
            return False
    
    def get_domain_from_url(self, url: str) -> Optional[str]:
        """
        Extract domain from URL for whitelist checking.
        
        Args:
            url: Image URL
            
        Returns:
            Domain name or None if invalid URL
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() if parsed.netloc else None
        except Exception:
            return None
