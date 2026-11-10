import os
from getpass import getpass
from urllib.parse import urljoin

from core import NotLoggedInException
from core.challange import Challenge
from ctfs.ctf import CTF
from ctfs.ctfd import BadUserNameOrPasswordException


class SiberLab(CTF):
    """Puller for the SiberLab Attack & Defense platform (JWT API)."""

    def __init__(self, url, max_size=100, force=False):
        super().__init__(url, max_size, force)
        self.username = ""
        self.password = ""
        self.token = ""

    @staticmethod
    def apply_argparser(argument_parser):
        argument_parser.add_argument("-u", "--username", help="username")
        argument_parser.add_argument("-p", "--password", help="password")
        argument_parser.usage += "[-u USERNAME] [-p PASSWORD] "

    def login(self, sys_args, no_login=False, **kwargs):
        if no_login:
            return

        username = sys_args.get("username")
        password = sys_args.get("password")
        if not username or not password:
            username = os.getenv("CTF_USERNAME", input("User/Email: "))
            password = os.getenv("CTF_PASSWORD", getpass("Password: ", stream=None))

        res = self.session.post(
            urljoin(self.url, "/api/login"),
            json={"username": username, "password": password},
        )

        if not res.ok:
            raise BadUserNameOrPasswordException()

        self.token = res.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.username = username
        self.password = password

    def __get_attachment_url(self, attachment):
        if not attachment:
            return None
        if attachment.startswith(("http://", "https://")):
            return attachment
        return urljoin(self.url, attachment)

    def iter_challenges(self):
        res = self.session.get(urljoin(self.url, "/api/challenges"))
        if res.status_code == 401:
            raise NotLoggedInException()
        res.raise_for_status()

        for challenge in res.json():
            categories = challenge.get("categories") or []
            attachment = self.__get_attachment_url(challenge.get("attachment"))
            yield Challenge(
                ctf=self,
                name=challenge.get("title") or challenge["name"],
                category=challenge.get("category") or ", ".join(categories),
                description=challenge.get("description", ""),
                files=[attachment] if attachment else [],
            )

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
