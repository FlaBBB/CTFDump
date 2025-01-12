import os
from getpass import getpass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core import NotLoggedInException
from core.challange import Challenge
from core.ctfs.ctf import CTF


class BadUserNameOrPasswordException(Exception):
    pass


class GZctf(CTF):
    def __init__(self, url):
        super().__init__(url)
        self.username = ""
        self.password = ""
        self.game_id = None

    @staticmethod
    def apply_argparser(parser):
        parser.add_argument("-id", "--game-id", help="game id")
        parser.add_argument("-u", "--username", help="username")
        parser.add_argument("-p", "--password", help="password")
        parser.usage += "[-id GAME-ID] [-u USERNAME] [-p PASSWORD] "

    def login(self, sys_args, no_login=False, **kwargs):
        if no_login:
            return

        username = sys_args.get("username")
        password = sys_args.get("password")
        if not username or not password:
            username = os.getenv("CTF_USERNAME", input("User/Email: "))
            password = os.getenv("CTF_PASSWORD", getpass("Password: ", stream=None))

        game_id = sys_args.get("game_id")
        if not game_id:
            game_id = input("Game ID: ")

        res = self.session.post(
            url=urljoin(self.url, "api/account/login"),
            json={"userName": username, "password": password},
        )

        if not res.ok:
            raise BadUserNameOrPasswordException()

        self.username = username
        self.password = password
        self.game_id = game_id

    def __get_file_url(self, file_name):
        if not file_name.startswith("/files/"):
            file_name = f"/files/{file_name}"
        return urljoin(self.url, file_name)

    def __get_details_challenge(self, challenge_id):
        return self.session.get(
            urljoin(self.url, f"/api/game/{self.game_id}/challenges/{challenge_id}")
        ).json()

    def iter_challenges(self):
        details = self.session.get(
            urljoin(self.url, f"/api/game/{self.game_id}/details")
        ).json()
        challenges = details["challenges"]
        for category in challenges.keys():
            for challenge in challenges[category]:
                challenge = self.__get_details_challenge(challenge["id"])
                yield Challenge(
                    ctf=self,
                    name=challenge["title"],
                    category=challenge["tag"],
                    description=challenge["content"],
                    files=(
                        [self.url + challenge["context"]["url"].strip("/")]
                        if challenge["context"]["url"]
                        else []
                    ),
                )

    def credential_to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "game_id": self.game_id,
        }

    def credential_from_dict(self, credential):
        self.username = credential["username"]
        self.password = credential["password"]
        self.game_id = credential["game_id"]
