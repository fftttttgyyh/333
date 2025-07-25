"""TikTok downloader"""

import re
import json
import asyncio
from typing import Dict, Any
from .base import BaseDownloader
from config import Config

class TikTokDownloader(BaseDownloader):
    """TikTok video and photo downloader"""
    
    def can_handle(self, url: str) -> bool:
        """Check if URL is from TikTok"""
        tiktok_patterns = [
            r'tiktok\.com',
            r'vm\.tiktok\.com',
            r'vt\.tiktok\.com'
        ]
        return any(re.search(pattern, url.lower()) for pattern in tiktok_patterns)
    
    async def download(self, url: str) -> Dict[str, Any]:
        """Download content from TikTok URL"""
        try:
            # Get video info and download URL
            video_info = await self._get_video_info(url)
            if not video_info['success']:
                return video_info
            
            # Download the video file
            filename = f"tiktok_{video_info['video_id']}.mp4"
            file_path = await self.download_file(video_info['download_url'], filename)
            
            # Check file size
            import os
            file_size = os.path.getsize(file_path)
            if file_size > Config.MAX_VIDEO_SIZE:
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
                'media_type': 'video',
                'title': video_info.get('title', 'TikTok Video'),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"TikTok download failed: {str(e)}",
                'file_path': None,
                'media_type': None
            }
    
    async def _get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract video information from TikTok URL"""
        try:
            session = await self.get_session()
            
            # First, resolve the URL if it's shortened
            async with session.get(url, allow_redirects=True) as response:
                final_url = str(response.url)
            
            # Extract video ID from URL
            video_id_match = re.search(r'/video/(\d+)', final_url)
            if not video_id_match:
                return {
                    'success': False,
                    'error': "Could not extract video ID from URL"
                }
            
            video_id = video_id_match.group(1)
            
            # Get video page content
            async with session.get(final_url) as response:
                if response.status != 200:
                    return {
                        'success': False,
                        'error': f"Failed to access TikTok page: HTTP {response.status}"
                    }
                
                content = await response.text()
                
                # Extract video data from page script
                script_match = re.search(r'<script id="SIGI_STATE"[^>]*>(.*?)</script>', content)
                if not script_match:
                    return {
                        'success': False,
                        'error': "Could not find video data in page"
                    }
                
                try:
                    data = json.loads(script_match.group(1))
                    video_data = data.get('ItemModule', {}).get(video_id, {})
                    
                    if not video_data:
                        return {
                            'success': False,
                            'error': "Video data not found"
                        }
                    
                    # Extract download URL
                    video_obj = video_data.get('video', {})
                    download_url = video_obj.get('downloadAddr') or video_obj.get('playAddr')
                    
                    if not download_url:
                        return {
                            'success': False,
                            'error': "Could not find video download URL"
                        }
                    
                    return {
                        'success': True,
                        'video_id': video_id,
                        'download_url': download_url,
                        'title': video_data.get('desc', 'TikTok Video')
                    }
                    
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': "Failed to parse video data"
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to get video info: {str(e)}"
            }
