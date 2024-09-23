import os
from getpass import getpass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from core import NotLoggedInException
from core.challange import Challenge
from core.ctfs.ctf import CTF


class BadUserNameOrPasswordException(Exception):
    pass


class CTFd(CTF):
    def __init__(self, url):
        super().__init__(url)
        self.username = ""
        self.password = ""

    @staticmethod
    def apply_argparser(argument_parser):
        argument_parser.add_argument("-u", "--username", help="username")
        argument_parser.add_argument("-p", "--password", help="password")
        argument_parser.usage += "[-u USERNAME] [-p PASSWORD] "

    @property
    def version(self):
        # CTFd >= v2
        res = self.session.get(urljoin(self.url, "/api/v1/challenges"))
        if res.status_code == 403:
            # Unknown (Not logged In)
            return -1

        if res.status_code != 404:
            return 2

        # CTFd  >= v1.2
        res = self.session.get(urljoin(self.url, "/chals"))
        if res.status_code == 403:
            # Unknown (Not logged In)
            return -1

        if "description" not in res.json()["game"][0]:
            return 1

        # CTFd  <= v1.1
        return 0

    def __get_nonce(self):
        res = self.session.get(urljoin(self.url, "/login"))
        html = BeautifulSoup(res.text, "html.parser")
        return html.find("input", {"type": "hidden", "name": "nonce"}).get("value")

    def login(self, sys_args, no_login=False, **kwargs):
        if no_login:
            return

        username = sys_args.get("username")
        password = sys_args.get("password")
        if not username or not password:
            username = os.getenv("CTF_USERNAME", input("User/Email: "))
            password = os.getenv("CTF_PASSWORD", getpass("Password: ", stream=None))

        next_url = "/challenges"
        res = self.session.post(
            url=urljoin(self.url, "/login"),
            params={"next": next_url},
            data={"name": username, "password": password, "nonce": self.__get_nonce()},
        )

        if res.ok and urlparse(res.url).path != next_url:
            raise BadUserNameOrPasswordException()

        self.username = username
        self.password = password

    def __get_file_url(self, file_name):
        if not file_name.startswith("/files/"):
            file_name = f"/files/{file_name}"
        return urljoin(self.url, file_name)

    def __iter_challenges(self):
        version = self.version
        if version < 0:
            raise NotLoggedInException()

        if version >= 2:
            res_json = self.session.get(urljoin(self.url, "/api/v1/challenges")).json()
            challenges = res_json["data"]
            for challenge in challenges:
                challenge_json = self.session.get(
                    urljoin(self.url, f"/api/v1/challenges/{challenge['id']}")
                ).json()
                yield challenge_json["data"]

            return

        res_json = self.session.get(urljoin(self.url, "/chals")).json()
        challenges = res_json["game"]
        for challenge in challenges:
            if version >= 1:
                yield self.session.get(
                    urljoin(self.url, f"/chals/{challenge['id']}")
                ).json()
                continue

            yield challenge

    def iter_challenges(self):
        for challenge in self.__iter_challenges():
            yield Challenge(
                ctf=self,
                name=challenge["name"],
                category=challenge["category"],
                description=challenge["description"],
                files=list(map(self.__get_file_url, challenge.get("files", []))),
            )

    def credential_to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
        }

    def credential_from_dict(self, credential):
        self.username = credential["username"]
        self.password = credential["password"]
