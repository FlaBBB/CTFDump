import codecs
import json
import logging
import os
import ssl
from getpass import getpass
from os import path
from typing import Any, Generator, List
from urllib.parse import urljoin, urlparse

from cloudscraper import create_scraper

from core.challange import Challenge
from core.ctfs.ctf import CTF
from core.ctfs.ctfd import BadUserNameOrPasswordException


class NotCompatiblePlatformException(Exception):
    pass


class AD(CTF):
    def __init__(self, url):
        if self.__class__.__name__ == "CTF":
            raise NotCompatiblePlatformException()

        self.name = self.__class__.__name__
        self.url = url
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        self.session = create_scraper(ssl_context=ssl_context)
        self.logger = logging.getLogger(__name__)
        self.challanges: List[Challenge] = []

    @staticmethod
    def apply_argparser(argument_parser) -> None:
        argument_parser.add_argument("-u", "--username", help="username")
        argument_parser.add_argument("-p", "--password", help="password")
        argument_parser.usage += "[-u USERNAME] [-p PASSWORD] "

    def __iter_challenges(self):
        res_json = self.session.get(urljoin(self.url, "/api/challenge")).json()
        return res_json["data"]

    def iter_challenges(self):
        for challenge in self.__iter_challenges():
            yield Challenge(
                ctf=self,
                name=challenge["name"],
                category="Attack Defense",
                description=challenge["description"],
                files=[challenge["attachment"]],
            )

    def login(self, sys_args, no_login=False, **kwargs) -> None:
        if no_login:
            return

        username = sys_args.get("username")
        password = sys_args.get("password")
        if not username or not password:
            username = os.getenv("CTF_USERNAME", input("User/Email: "))
            password = os.getenv("CTF_PASSWORD", getpass("Password: ", stream=None))

        next_url = "/challenges"
        res = self.session.post(
            url=urljoin(self.url, "/api/user/login"),
            params={"next": next_url},
            data={"email": username, "password": password},
            verify=False,
        )

        res_data = res.json()
        if not res.ok  or not res_data.get("success", False):
            raise BadUserNameOrPasswordException()

        self.session.headers.update(
            {"Authorization": f"Bearer {res_data['data']['token']}"}
        )

        self.username = username
        self.password = password

    def credential_to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
        }

    def credential_from_dict(self, credential):
        self.username = credential["username"]
        self.password = credential["password"]

    def logout(self):
        self.session.headers.pop("Authorization", None)
