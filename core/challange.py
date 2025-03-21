import codecs
import logging
import os
import re
from os import path

from downloader import DownloadManager


class Challenge(object):
    def __init__(self, ctf, name, category="", description="", files=None, value=0):
        self.ctf = ctf
        self.name = name
        self.category = category
        self.description = description
        self.logger = logging.getLogger(__name__)
        self.files = self.collect_files(files, description)
        self.value = value

    def __str__(self):
        return f'<"{self.name}" ({self.category} - {self.value})>'

    def __repr__(self):
        return self.__str__()

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
    def from_dict(data, ctfs):
        return Challenge(
            ctf=ctfs,
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

    def download_all_files(self):
        manager = DownloadManager.get_instance()
        for file_url in self.files:
            try:
                manager.download(file_url, self.get_challenge_path())
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
