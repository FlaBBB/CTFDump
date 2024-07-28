import codecs
import json
import logging
from os import path
from typing import List
from urllib.parse import urljoin

from cloudscraper import create_scraper

from core.challange import Challenge


class NotCompatiblePlatformException(Exception):
    pass


class CTF(object):
    def __init__(self, url):
        if self.__class__.__name__ == "CTF":
            raise NotCompatiblePlatformException()

        self.name = self.__class__.__name__
        self.url = url
        self.session = create_scraper()
        self.logger = logging.getLogger(__name__)
        self.challanges: List[Challenge] = []

    @staticmethod
    def apply_argparser(argument_parser):
        raise NotImplementedError()

    def iter_challenges(self):
        raise NotImplementedError()

    def login(self, no_login=False, **kwargs):
        raise NotImplementedError()

    def credential_to_dict(self):
        raise NotImplementedError()

    def credential_from_dict(self, credential):
        raise NotImplementedError()

    def logout(self):
        self.session.get(urljoin(self.url, "/logout"))

    def save_config(self):
        if self.name == "CTF":
            raise NotCompatiblePlatformException()

        with codecs.open("config.json", "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "platform": self.name,
                        "url": self.url,
                        "credentials": self.credential_to_dict(),
                        "challenges": [
                            challenge.to_dict() for challenge in self.challanges
                        ],
                    },
                    indent=4,
                )
            )

    def load_config(self, config_path="config.json") -> bool:
        if not path.exists(config_path):
            return False

        with codecs.open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config["platform"] != self.name or config["url"] != self.url:
                raise NotCompatiblePlatformException()

            self.credential_from_dict(config["credentials"])

            for challenge in config["challenges"]:
                self.challanges.append(Challenge.from_dict(challenge, self))

        return True

    def save(self):
        self.challanges = list(self.iter_challenges())
        for challenge in self.challanges:
            challenge.dump()
            challenge.download_all_files()

        self.save_config()

    def update(self, force=False):
        new_challange = list(self.iter_challenges())
        is_changed = False
        for nc, oc in zip(new_challange, self.challanges):
            if nc != oc:
                nc.dump()
                nc.download_all_files(force)
                is_changed = True

        if is_changed:
            self.challanges = new_challange
            self.save_config()
        else:
            self.logger.info("No changes found")
