import os
import re
from typing import List, Optional
from urllib.parse import urlparse

import tqdm

from core import helper
from downloader.drive import Drive

SOURCES: List = [Drive]


class FailedToDownloadFile(Exception):
    """Raised when a file download fails"""

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

    def __init__(self, session, logger, is_force: bool, max_size: int):
        self.session = session
        self.logger = logger
        self.is_force = is_force
        self.max_size_bytes = max_size * 1024 * 1024

    @staticmethod
    def init(session, logger, is_force: bool, max_size: int):
        assert (
            DownloadManager._instance is None
        ), "DownloadManager is already initialized"

        DownloadManager._instance = DownloadManager(session, logger, is_force, max_size)

    @staticmethod
    def get_instance():
        assert (
            DownloadManager._instance is not None
        ), "DownloadManager is not initialized"

        return DownloadManager._instance

    def download_with_progress(
        self, response, path: str, filename: str, total_size: Optional[int]
    ) -> None:
        """
        Download file with progress bar

        Args:
            response: Response object with download data
            path: Download directory path
            filename: Output filename
            total_size: Total file size in bytes, might be None for text content
        """
        filepath = os.path.join(path, filename)

        if self._should_skip_download(filepath, filename, total_size):
            return

        if total_size is None:
            self.logger.info(f"Downloading {filename} (Unknown size)")
            self._download_file_without_size(response, filepath, filename)
        else:
            self.logger.info(
                f"Downloading {filename} ({helper.size_converter(total_size)})"
            )
            self._download_file_with_size(response, filepath, filename, total_size)

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
            self.logger.warning(f"Warning: {filename} might be a text file")

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
        self._handle_direct_download(url, path)

    def _handle_direct_download(self, url: str, path: str) -> None:
        """Handle direct URL download when no source matches"""
        filename = self.escape_filename(os.path.basename(urlparse(url).path))
        size = self._get_url_size(url)

        self._log_download_start(filename, size)
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

    def _get_url_size(self, url: str) -> Optional[int]:
        """Get file size from URL using HEAD request"""
        return self.session.head(url).headers.get("Content-Length")

    def _should_skip_download(
        self, filepath: str, filename: str, total_size: Optional[int]
    ) -> bool:
        """Check if download should be skipped"""
        if os.path.exists(filepath) and not self.is_force:
            self.logger.info(f"Skipping \"{filename}\" (already downloaded)")
            return True

        if total_size and total_size > self.max_size_bytes:
            self.logger.info(
                f"Skipping \"{filename}\" with size {helper.size_converter(total_size)} (size too large)"
            )
            return True

        return False

    def _download_file_with_size(
        self, response, filepath: str, filename: str, total_size: int
    ) -> None:
        """Download file with known size using progress bar"""
        with open(filepath, "wb") as file, tqdm.tqdm(
            desc=f"Downloading {filename}",
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
            desc=f"Downloading {filename}",
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
            f"Downloaded {filename} ({helper.size_converter(downloaded_size)})"
        )

    def _log_download_start(self, filename: str, size: Optional[int]) -> None:
        """Log download start with file info"""
        if size is None:
            self.logger.info(f"Downloading {filename} (Unknown size)")
        else:
            self.logger.info(f"Downloading {filename} ({helper.size_converter(size)})")
