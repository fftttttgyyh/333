"""URL parsing and validation utilities"""

import re
from typing import Optional
from urllib.parse import urlparse

class URLParser:
    """Utility class for parsing and validating URLs"""
    
    @staticmethod
    def extract_platform(url: str) -> Optional[str]:
        """Extract platform name from URL"""
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in ['youtube.com', 'youtu.be']):
            return 'youtube'
        elif any(domain in url_lower for domain in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
            return 'tiktok'
        elif any(domain in url_lower for domain in ['instagram.com', 'instagr.am']):
            return 'instagram'
        elif any(domain in url_lower for domain in ['pinterest.com', 'pinterest.', 'pin.it']):
            return 'pinterest'
        else:
            return None
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL for processing"""
        # Remove tracking parameters and fragments
        url = url.split('?')[0].split('#')[0]
        
        # Ensure https
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        elif not url.startswith('https://'):
            url = 'https://' + url
        
        return url
    
    @staticmethod
    def extract_youtube_video_id(url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_tiktok_video_id(url: str) -> Optional[str]:
        """Extract TikTok video ID from URL"""
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_instagram_shortcode(url: str) -> Optional[str]:
        """Extract Instagram shortcode from URL"""
        patterns = [
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def extract_pinterest_pin_id(url: str) -> Optional[str]:
        """Extract Pinterest pin ID from URL"""
        match = re.search(r'/pin/(\d+)', url)
        return match.group(1) if match else None
