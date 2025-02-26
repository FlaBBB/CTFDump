import os
import re
import tarfile
import time
import zipfile
from http.client import IncompleteRead
from typing import List, Optional
from urllib.parse import urlparse

import py7zr
import rarfile
import tqdm
from requests.exceptions import ConnectionError

from core import helper
from downloader.drive import DriveSource
from downloader.mediafire import MediafireSource

SOURCES: List = [DriveSource, MediafireSource]

class FailedToDownloadFile(Exception):
    """Raised when a file download fails"""
    pass

class FailedToExtractFile(Exception):
    """Raised when file extraction fails"""
    pass

class DownloadManager:
    _instance = None
    CHUNK_SIZE = 1024
    BINARY_CONTENT_TYPES = {
        "application/octet-stream",
        "application/zip",
        "application/x-rar-compressed",
        "application/pdf",
        "application/x-bzip2",
        "application/x-gzip",
        "image/",
        "video/",
        "audio/",
    }
    
    COMPRESSED_EXTENSIONS = {
        '.zip': 'zip',
        '.rar': 'rar',
        '.7z': '7z',
        '.tar': 'tar',
        '.tar.gz': 'tar.gz',
        '.tgz': 'tar.gz',
        '.tar.bz2': 'tar.bz2',
        '.tbz2': 'tar.bz2'
    }

    def __init__(self, session, logger, is_force: bool, max_size: int):
        self.session = session
        self.logger = logger
        self.is_force = is_force
        self.max_size_bytes = max_size * 1024 * 1024

    @staticmethod
    def init(session, logger, is_force: bool, max_size: int):
        assert DownloadManager._instance is None, "DownloadManager is already initialized"
        DownloadManager._instance = DownloadManager(session, logger, is_force, max_size)

    @staticmethod
    def get_instance():
        assert DownloadManager._instance is not None, "DownloadManager is not initialized"
        return DownloadManager._instance

    def _extract_file(self, filepath: str, extract_path: str) -> None:
        """
        Extract compressed file based on its extension
        
        Args:
            filepath: Path to compressed file
            extract_path: Directory to extract to
        """
        filename = os.path.basename(filepath)
        extension = self._get_compression_type(filepath)
        
        if not extension:
            return
            
        try:
            if extension == 'zip':
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                    
            elif extension == 'rar':
                with rarfile.RarFile(filepath, 'r') as rar_ref:
                    rar_ref.extractall(extract_path)
                    
            elif extension == '7z':
                with py7zr.SevenZipFile(filepath, 'r') as sz_ref:
                    sz_ref.extractall(extract_path)
                    
            elif 'tar' in extension:
                with tarfile.open(filepath) as tar_ref:
                    # Check for any harmful files before extraction
                    for member in tar_ref.getmembers():
                        if member.name.startswith(('/')) or '..' in member.name:
                            raise FailedToExtractFile(f"Potentially harmful file in archive: {member.name}")
                    tar_ref.extractall(extract_path)
                    
            self.logger.info(f'Successfully extracted "{filename}" to {extract_path}')
            
        except Exception as e:
            raise FailedToExtractFile(f'Failed to extract "{filename}": {str(e)}')

    def _get_compression_type(self, filepath: str) -> Optional[str]:
        """
        Determine compression type based on file extension
        
        Args:
            filepath: Path to file
            
        Returns:
            String indicating compression type or None if not compressed
        """
        for ext, comp_type in self.COMPRESSED_EXTENSIONS.items():
            if filepath.lower().endswith(ext):
                return comp_type
        return None

    def download_with_progress(self, response, path: str, filename: str, total_size: Optional[int], retries: int = 3) -> None:
        filepath = os.path.join(path, filename)

        if self._should_skip_download(filepath, filename, total_size):
            return

        self._log_download_start(filename, total_size)

        attempt = 0
        while attempt < retries:
            try:
                if total_size is None:
                    self._download_file_without_size(response, filepath, filename)
                else:
                    self._download_file_with_size(response, filepath, filename, total_size)
                
                # After successful download, check if it's compressed and extract
                if os.path.exists(filepath):
                    try:
                        self._extract_file(filepath, path)
                    except FailedToExtractFile as e:
                        self.logger.error(str(e))
                break
            except (ConnectionError, IncompleteRead) as e:
                attempt += 1
                self.logger.warning(f"Download failed: {e}. Retrying {attempt}/{retries}...")
                time.sleep(0.5)
        else:
            self.logger.error(f'Failed to download "{filename}" after {retries} attempts')

    def invoke(self, getable_url: str, path: str, filename: str) -> None:
        """
        Download file from direct URL

        Args:
            getable_url: Direct download URL
            path: Download directory path
            filename: Output filename
        """
        response = self._get_response(getable_url)
        total_size, is_binary = self._get_content_info(response)

        if not is_binary:
            self.logger.warning(f'Warning: "{filename}" might be a text file')

        self.download_with_progress(response, path, filename, total_size)

    def download(self, url: str, path: str) -> None:
        """
        Download file from URL using appropriate source

        Args:
            url: URL to download from
            path: Download directory path
        """
        # Ensure download directory exists
        os.makedirs(path, exist_ok=True)

        # Try specialized sources first
        for source_class in SOURCES:
            source = source_class(self, self.session)
            if source.is_valid(url):
                source.download(url, path)
                return

        # Fall back to direct download
        self.direct_download(url, path)

    def direct_download(self, url: str, path: str) -> None:
        """Handle direct URL download when no source matches"""
        filename = self.escape_filename(os.path.basename(urlparse(url).path))

        self.invoke(url, path, filename)

    @staticmethod
    def escape_filename(filename: str) -> str:
        """Clean filename to be filesystem-safe"""
        return re.sub(r"[^\w\s\-.()]", "", filename.strip()).replace(" ", "_")

    def _get_content_info(self, response) -> tuple[Optional[int], bool]:
        """Get content length and determine if content is binary"""
        content_type = response.headers.get("Content-Type", "").lower()
        is_binary = any(
            type_prefix in content_type for type_prefix in self.BINARY_CONTENT_TYPES
        )

        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                return int(content_length), is_binary
            except ValueError:
                pass

        return None, is_binary

    def _get_response(self, url: str):
        """Get response from URL with error handling"""
        response = self.session.get(url, stream=True)
        if response.status_code != 200:
            raise FailedToDownloadFile(f"Failed to download from {url}")
        return response

    def _should_skip_download(
        self, filepath: str, filename: str, total_size: Optional[int]
    ) -> bool:
        """Check if download should be skipped"""
        if os.path.exists(filepath) and not self.is_force:
            self.logger.info(f'Skipping "{filename}" (already downloaded)')
            return True

        if total_size and total_size > self.max_size_bytes:
            self.logger.info(
                f'Skipping "{filename}" with size {helper.size_converter(total_size)} (size too large)'
            )
            return True

        return False

    def _download_file_with_size(
        self, response, filepath: str, filename: str, total_size: int
    ) -> None:
        """Download file with known size using progress bar"""
        with open(filepath, "wb") as file, tqdm.tqdm(
            desc=f'Downloading "{filename}"',
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        ) as bar:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                size = file.write(chunk)
                bar.update(size)

    def _download_file_without_size(
        self, response, filepath: str, filename: str
    ) -> None:
        """Download file with unknown size using simplified progress"""
        downloaded_size = 0
        with open(filepath, "wb") as file, tqdm.tqdm(
            desc=f'Downloading "{filename}"',
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=False,
        ) as bar:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                size = file.write(chunk)
                downloaded_size += size
                bar.update(size)

        self.logger.info(
            f'Downloaded "{filename}" ({helper.size_converter(downloaded_size)})'
        )

    def _log_download_start(self, filename: str, size: Optional[int]) -> None:
        """Log download start with file info"""
        if size is None:
            self.logger.info(f'Downloading "{filename}" (Unknown size)')
        else:
            self.logger.info(
                f'Downloading "{filename}" ({helper.size_converter(size)})'
            )
