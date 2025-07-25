"""Instagram downloader"""

import re
import json
from typing import Dict, Any
from .base import BaseDownloader
from config import Config

class InstagramDownloader(BaseDownloader):
    """Instagram photo and video downloader"""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from Instagram"""
        instagram_patterns = [
            r'instagram\.com',
            r'instagr\.am'
        ]
        return any(re.search(pattern, url.lower()) for pattern in instagram_patterns)
    
    async def download(self, url: str) -> Dict[str, Any]:
        """Download content from Instagram URL"""
        try:
            # Get media info
            media_info = await self._get_media_info(url)
            if not media_info['success']:
                return media_info
            
            # Determine file extension and media type
            media_url = media_info['media_url']
            is_video = media_info['is_video']
            
            if is_video:
                filename = f"instagram_{media_info['media_id']}.mp4"
                media_type = 'video'
                size_limit = Config.MAX_VIDEO_SIZE
            else:
                filename = f"instagram_{media_info['media_id']}.jpg"
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
                'title': media_info.get('caption', 'Instagram Media'),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Instagram download failed: {str(e)}",
                'file_path': None,
                'media_type': None
            }
    
    async def _get_media_info(self, url: str) -> Dict[str, Any]:
        """Extract media information from Instagram URL"""
        try:
            session = await self.get_session()
            
            # Convert to embed URL for easier parsing
            shortcode_match = re.search(r'/p/([A-Za-z0-9_-]+)', url)
            if not shortcode_match:
                shortcode_match = re.search(r'/reel/([A-Za-z0-9_-]+)', url)
            
            if not shortcode_match:
                return {
                    'success': False,
                    'error': "Could not extract media shortcode from URL"
                }
            
            shortcode = shortcode_match.group(1)
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
            
            # Get embed page content
            async with session.get(embed_url) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f"Failed to access Instagram embed: HTTP {response.status}"
                    }
                
                content = await response.text()
                
                # Look for media data in the page
                script_match = re.search(r'window\.__additionalDataLoaded\([^,]+,({.*?})\);', content)
                if not script_match:
                    # Try alternative pattern
                    script_match = re.search(r'"GraphImage"[^}]+display_url":"([^"]+)"', content)
                    if script_match:
                        return {
                            'success': True,
                            'media_id': shortcode,
                            'media_url': script_match.group(1).replace('\\u0026', '&'),
                            'is_video': False,
                            'caption': 'Instagram Photo'
                        }
                    
                    # Try video pattern
                    script_match = re.search(r'"GraphVideo"[^}]+video_url":"([^"]+)"', content)
                    if script_match:
                        return {
                            'success': True,
                            'media_id': shortcode,
                            'media_url': script_match.group(1).replace('\\u0026', '&'),
                            'is_video': True,
                            'caption': 'Instagram Video'
                        }
                    
                    return {
                        'success': False,
                        'error': "Could not find media data in embed page"
                    }
                
                try:
                    data = json.loads(script_match.group(1))
                    media_data = data.get('graphql', {}).get('shortcode_media', {})
                    
                    if not media_data:
                        return {
                            'success': False,
                            'error': "Media data not found in response"
                        }
                    
                    is_video = media_data.get('is_video', False)
                    if is_video:
                        media_url = media_data.get('video_url')
                    else:
                        media_url = media_data.get('display_url')
                    
                    if not media_url:
                        return {
                            'success': False,
                            'error': "Could not find media URL"
                        }
                    
                    caption = ""
                    edges = media_data.get('edge_media_to_caption', {}).get('edges', [])
                    if edges:
                        caption = edges[0].get('node', {}).get('text', '')
                    
                    return {
                        'success': True,
                        'media_id': shortcode,
                        'media_url': media_url,
                        'is_video': is_video,
                        'caption': caption[:100] + '...' if len(caption) > 100 else caption
                    }
                    
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': "Failed to parse media data"
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get media info: {str(e)}"
            }
