"""File handling utilities"""

import os
import mimetypes
from typing import Optional, Tuple
from config import Config

class FileHandler:
    """Utility class for file operations"""
    
    @staticmethod
    def get_file_info(file_path: str) -> Tuple[int, str, str]:
        """Get file size, MIME type, and extension"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        return file_size, mime_type or 'application/octet-stream', ext
    
    @staticmethod
    def is_valid_media_file(file_path: str) -> bool:
        """Check if file is a valid media file"""
        try:
            _, mime_type, ext = FileHandler.get_file_info(file_path)
            
            valid_video_types = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo']
            valid_image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            valid_extensions = ['.mp4', '.avi', '.mov', '.jpg', '.jpeg', '.png', '.gif', '.webp']
            
            return (mime_type in valid_video_types + valid_image_types) or (ext in valid_extensions)
        except:
            return False
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_hours: int = 24):
        """Clean up old files from directory"""
        import time
        
        if not os.path.exists(directory):
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                    except:
                        pass  # Ignore cleanup errors
    
    @staticmethod
    def ensure_telegram_compatibility(file_path: str) -> bool:
        """Check if file is compatible with Telegram limits"""
        try:
            file_size, mime_type, ext = FileHandler.get_file_info(file_path)
            
            # Check file size limits
            if 'video' in mime_type:
                return file_size <= Config.MAX_VIDEO_SIZE
            elif 'image' in mime_type:
                return file_size <= Config.MAX_PHOTO_SIZE
            else:
                return False
        except:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Generate a safe filename for the filesystem"""
        import re
        
        # Remove or replace unsafe characters
        safe_filename = re.sub(r'[^\w\s.-]', '', filename)
        safe_filename = re.sub(r'[-\s]+', '-', safe_filename)
        
        # Limit length
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename or 'media'
