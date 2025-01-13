import os
import re
from typing import Dict, Optional, Union

from bs4 import BeautifulSoup

from core.helper import size_converter
from downloader.base import BaseSource


class DriveSource(BaseSource):
    BASE_URL = "https://drive.usercontent.google.com/download"
    FILE_PATTERNS = [r"drive\.google\.com/file/d/.*", r"drive\.google\.com/open\?id=.*"]

    def download(self, url: str, path: str) -> None:
        """
        Download file from Google Drive

        Args:
            url: Google Drive sharing URL
        """
        file_id = self._extract_file_id(url)
        response = self._get_download_response(file_id)

        # Get file metadata
        filename = self._parse_filename(response)
        filesize = self._parse_filesize(response)

        # Handle download warning token if present
        params = {"id": file_id}
        if token := self._get_warning_token(response):
            params["confirm"] = token

        # Download the file
        self.manager.download_with_progress(response, path, filename, filesize)

    def is_valid(self, url: str) -> bool:
        """Check if URL is a valid Google Drive link"""
        return any(re.search(pattern, url) for pattern in self.FILE_PATTERNS)

    def _get_download_response(self, file_id: str):
        """Get download response, handling size bypass if needed"""
        params = {"id": file_id}
        response = self.session.get(self.BASE_URL, params=params, stream=True)

        # Handle size bypass if needed
        if response.headers["Content-Type"] != "application/octet-stream":
            bypass_params = self._parse_size_bypass_params(response)
            params.update(bypass_params)
            response = self.session.get(self.BASE_URL, params=params, stream=True)

        return response

    @staticmethod
    def _extract_file_id(url: str) -> str:
        """Extract file ID from Google Drive URL"""
        if "id=" in url:
            return url.split("id=")[1]
        elif "file/d/" in url:
            return url.split("file/d/")[1].split("/")[0]
        raise ValueError("Invalid Google Drive URL format")

    @staticmethod
    def _get_warning_token(response) -> Optional[str]:
        """Extract download warning token from cookies if present"""
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                return value
        return None

    @staticmethod
    def _parse_size_bypass_params(response) -> Dict[str, str]:
        """Parse hidden form inputs for size bypass"""
        soup = BeautifulSoup(response.text, "lxml")
        inputs = soup.find_all("input")
        return {
            input_["name"]: input_["value"]
            for input_ in inputs
            if input_["type"] == "hidden"
        }

    def _parse_filename(self, response) -> str:
        """Extract filename from response"""
        # Try Content-Disposition header first
        if cd := response.headers.get("Content-Disposition"):
            if match := re.search(r'filename="(.*)"', cd):
                return match.group(1)

        # Fall back to parsing HTML
        print(response.text)
        return self._find_in_html("a", response.text, -4)

    def _parse_filesize(self, response) -> float:
        """Extract filesize from response"""
        # Try Content-Length header first
        if content_length := response.headers.get("Content-Length"):
            return float(content_length)

        # Fall back to parsing HTML
        if size_text := self._find_in_html("span", response.text, -1):
            return self._convert_size_text(size_text)

        return 0

    @staticmethod
    def _find_in_html(tag: str, html: str, offset: int) -> str:
        """Find element in HTML at specific offset"""
        soup = BeautifulSoup(html, "lxml")
        if matches := soup.find_all(tag):
            return matches[offset].text
        return ""

    @staticmethod
    def _convert_size_text(size_text: str) -> float:
        """Convert size text (e.g., '1.5M' or '2.1G') to bytes"""
        size = size_text.split()[-1][1:-1]  # Extract size value and unit
        value = float(size[:-1])

        if "M" in size:
            return value * 10**6
        elif "G" in size:
            return value * 10**9
        return value
