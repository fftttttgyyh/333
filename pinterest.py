"""Pinterest downloader"""

import re
import json
from typing import Dict, Any
from .base import BaseDownloader
from config import Config

class PinterestDownloader(BaseDownloader):
    """Pinterest photo and video downloader"""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from Pinterest"""
        pinterest_patterns = [
            r'pinterest\.com',
            r'pinterest\.[a-z]+',
            r'pin\.it'
        ]
        return any(re.search(pattern, url.lower()) for pattern in pinterest_patterns)
    
    async def download(self, url: str) -> Dict[str, Any]:
        """Download content from Pinterest URL"""
        try:
            # Get pin info
            pin_info = await self._get_pin_info(url)
            if not pin_info['success']:
                return pin_info
            
            # Determine file type and extension
            media_url = pin_info['media_url']
            is_video = pin_info['is_video']
            
            if is_video:
                filename = f"pinterest_{pin_info['pin_id']}.mp4"
                media_type = 'video'
                size_limit = Config.MAX_VIDEO_SIZE
            else:
                # Determine image extension from URL
                if '.jpg' in media_url.lower() or '.jpeg' in media_url.lower():
                    ext = 'jpg'
                elif '.png' in media_url.lower():
                    ext = 'png'
                else:
                    ext = 'jpg'  # default
                
                filename = f"pinterest_{pin_info['pin_id']}.{ext}"
                media_type = 'photo'
                size_limit = Config.MAX_PHOTO_SIZE
            
            # Download the file
            file_path = await self.download_file(media_url, filename)
            
            # Check file size
            import os
            file_size = os.path.getsize(file_path)
            if file_size > size_limit:
                self.cleanup_file(file_path)
                return {
                    'success': False,
                    'error': f"File too large ({file_size / 1024 / 1024:.1f}MB)",
                    'file_path': None,
                    'media_type': None
                }
            
            return {
                'success': True,
                'file_path': file_path,
                'media_type': media_type,
                'title': pin_info.get('title', 'Pinterest Media'),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Pinterest download failed: {str(e)}",
                'file_path': None,
                'media_type': None
            }
    
    async def _get_pin_info(self, url: str) -> Dict[str, Any]:
        """Extract pin information from Pinterest URL"""
        try:
            session = await self.get_session()
            
            # Handle pin.it redirects
            if 'pin.it' in url:
                async with session.get(url, allow_redirects=True) as response:
                    url = str(response.url)
            
            # Extract pin ID from URL
            pin_id_match = re.search(r'/pin/(\d+)', url)
            if not pin_id_match:
                return {
                    'success': False,
                    'error': "Could not extract pin ID from URL"
                }
            
            pin_id = pin_id_match.group(1)
            
            # Get pin page content
            headers = {
                'User-Agent': Config.USER_AGENT,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f"Failed to access Pinterest page: HTTP {response.status}"
                    }
                
                content = await response.text()
                
                # Look for pin data in the page scripts
                script_matches = re.findall(r'<script[^>]*>([^<]*)</script>', content, re.DOTALL)
                
                for script in script_matches:
                    if 'pinterestapp:pins' in script or '"Pin"' in script:
                        # Try to extract JSON data
                        json_match = re.search(r'\{[^}]*"images"[^}]*\}', script)
                        if json_match:
                            try:
                                # Find the media URL in various possible formats
                                url_match = re.search(r'"url":\s*"([^"]+\.(?:jpg|jpeg|png|mp4|webm)[^"]*)"', script)
                                if url_match:
                                    media_url = url_match.group(1).replace('\\/', '/')
                                    is_video = any(ext in media_url.lower() for ext in ['.mp4', '.webm'])
                                    
                                    # Try to extract title
                                    title_match = re.search(r'"title":\s*"([^"]*)"', script)
                                    title = title_match.group(1) if title_match else "Pinterest Media"
                                    
                                    return {
                                        'success': True,
                                        'pin_id': pin_id,
                                        'media_url': media_url,
                                        'is_video': is_video,
                                        'title': title[:100] + '...' if len(title) > 100 else title
                                    }
                            except:
                                continue
                
                # Fallback: look for og:image meta tag
                og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', content)
                if og_image_match:
                    media_url = og_image_match.group(1)
                    return {
                        'success': True,
                        'pin_id': pin_id,
                        'media_url': media_url,
                        'is_video': False,
                        'title': "Pinterest Image"
                    }
                
                return {
                    'success': False,
                    'error': "Could not find media data in Pinterest page"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get pin info: {str(e)}"
            }
