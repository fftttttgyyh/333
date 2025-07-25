"""Base downloader class with common functionality"""

import os
import aiohttp
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from config import Config

class BaseDownloader(ABC):
    """Abstract base class for all platform downloaders"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.download_dir = Config.DOWNLOAD_DIR
        self._ensure_download_dir()
    
    def _ensure_download_dir(self):
        """Ensure download directory exists"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT),
                headers={"User-Agent": Config.USER_AGENT}
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @abstractmethod
    async def download(self, url: str) -> Dict[str, Any]:
        """
        Download media from URL
        Returns: Dict with 'success', 'file_path', 'media_type', 'error' keys
        """
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this downloader can handle the given URL"""
        pass
    
    async def download_file(self, url: str, filename: str) -> str:
        """Download file from URL and save to local filesystem"""
        session = await self.get_session()
        file_path = os.path.join(self.download_dir, filename)
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            file.write(chunk)
                    return file_path
                else:
                    raise Exception(f"HTTP {response.status}: Failed to download file")
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
    
    def cleanup_file(self, file_path: str):
        """Remove downloaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass  # Ignore cleanup errors
