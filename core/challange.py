import codecs
import logging
import os
import re
from os import path
from urllib.parse import urlparse

from . import helper


class Challenge(object):
    def __init__(self, ctf, name, category="", description="", files=None, value=0):
        self.ctf = ctf
        self.name = name
        self.category = category
        self.description = description
        self.logger = logging.getLogger(__name__)
        self.files = self.collect_files(files, description)
        self.value = value

    def __eq__(self, value: object) -> bool:
        return (
            self.name == value.name
            and self.category == value.category
            and self.description == value.description
            and self.files == value.files
            and self.value == value.value
        )

    def to_dict(self):
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "files": self.files,
            "value": self.value,
        }

    @staticmethod
    def from_dict(data):
        return Challenge(
            name=data["name"],
            category=data["category"],
            description=data["description"],
            files=data["files"],
            value=data["value"],
        )

    @staticmethod
    def collect_files(files, description=""):
        files = files or []
        files.extend(
            re.findall(
                r"https?:\/\/\w+(?:\.\w+)+(?:\/[?=&\w._-]+)+", description, re.DOTALL
            )
        )
        return files

    @staticmethod
    def escape_filename(filename):
        return re.sub(r"[^\w\s\-.()]", "", filename.strip()).replace(" ", "_")

    def get_challenge_path(self):
        return path.join(
            self.escape_filename(self.category), self.escape_filename(self.name)
        ).replace(" ", "_")

    def download_file(self, url, file_path, override=False):
        if "google.com" in url:
            helper.gdown(url, file_path, enable=override)
            return

        name = self.escape_filename(path.basename(urlparse(url).path))

        file_path = os.path.join(file_path, name)
        if not os.path.exists(file_path) or override:
            response = self.ctf.session.get(url, stream=True)
            helper.download(response, file_path)

    def download_all_files(self, force=False):
        for file_url in self.files:
            try:
                self.download_file(file_url, self.get_challenge_path(), force)
            except Exception as e:
                self.logger.error(f"Failed to download {file_url}: {e}")
                continue

    def dump(self):
        # Create challenge directory if not exist
        challenge_path = self.get_challenge_path()
        os.makedirs(challenge_path, exist_ok=True)

        with codecs.open(
            path.join(challenge_path, "ReadMe.md"), "wb", encoding="utf-8"
        ) as f:
            f.write(f"Name: {self.name}\n")
            f.write(f"Value: {self.value}\n")
            f.write(f"Description: {self.description}\n")
            self.logger.info(
                f"Creating Challenge [{self.category or 'No Category'}] {self.name}"
            )
