import codecs
import json
import logging
import os
import re
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from getpass import getpass
from os import path
from typing import List
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup
from cloudscraper import create_scraper
from requests.utils import CaseInsensitiveDict

import helper

__version__ = "0.3.0"


class BadUserNameOrPasswordException(Exception):
    pass


class BadTokenException(Exception):
    pass


class NotLoggedInException(Exception):
    pass


class UnknownFrameworkException(Exception):
    pass


class NotCompatiblePlatformException(Exception):
    pass


class Challenge(object):
    def __init__(self, ctf, name, category="", description="", files=None, value=0):
        self.ctf: CTF = ctf
        self.name = name
        self.value = value
        self.category = category
        self.description = description
        self.logger = logging.getLogger(__name__)
        self.files = self.collect_files(files, description)

    def __eq__(self, value: object) -> bool:
        return (
            self.name == value.name
            and self.category == value.category
            and self.description == value.description
            and self.files == value.files
            and self.value == value.value
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
            self.download_file(file_url, self.get_challenge_path(), force)

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


class CTF(object):
    def __init__(self, url):
        self.name = self.__class__.__name__
        self.url = url
        self.session = create_scraper()
        self.logger = logging.getLogger(__name__)
        self.challanges: List[Challenge] = []

    def iter_challenges(self):
        raise NotImplementedError()

    def login(self, **kwargs):
        raise NotImplementedError()

    def logout(self):
        self.session.get(urljoin(self.url, "/logout"))

    def load_config(self, config_path="config.json") -> bool:
        if not path.exists(config_path):
            return False

        with codecs.open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config["platform"] != self.name or config["url"] != self.url:
                raise NotCompatiblePlatformException()

            for challenge in config["challenges"]:
                chall = Challenge(
                    ctf=self,
                    name=challenge["name"],
                    category=challenge["category"],
                    description=challenge["description"],
                    files=None,
                    value=challenge["value"],
                )
                chall.files = challenge["files"]
                self.challanges.append(chall)

        return True

    def save_config(self):
        with codecs.open("config.json", "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "platform": self.name,
                        "url": self.url,
                        "challenges": [
                            {
                                "name": challenge.name,
                                "category": challenge.category,
                                "description": challenge.description,
                                "files": challenge.files,
                                "value": challenge.value,
                            }
                            for challenge in self.challanges
                        ],
                    },
                    indent=4,
                )
            )

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


class CTFd(CTF):
    def __init__(self, url):
        super().__init__(url)

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

    def login(self, username, password):
        next_url = "/challenges"
        res = self.session.post(
            url=urljoin(self.url, "/login"),
            params={"next": next_url},
            data={"name": username, "password": password, "nonce": self.__get_nonce()},
        )
        if res.ok and urlparse(res.url).path == next_url:
            return True
        return False

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


class rCTF(CTF):
    def __init__(self, url):
        super().__init__(url)
        self.BarerToken = ""

    @staticmethod
    def __get_file_url(file_info):
        return file_info["url"]

    def login(self, team_token):
        team_token = unquote(team_token)
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        res = self.session.post(
            url=urljoin(self.url, "/api/v1/auth/login"),
            headers=headers,
            data=json.dumps({"teamToken": team_token}),
        )

        if res.ok:
            self.BarerToken = json.loads(res.content)["data"]["authToken"]
            return True
        return False

    def __iter_challenges(self):
        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(self.BarerToken),
        }
        res_json = self.session.get(
            urljoin(self.url, "/api/v1/challs"), headers=headers
        ).json()
        challenges = res_json["data"]
        for challenge in challenges:
            yield challenge

    def iter_challenges(self):
        for challenge in self.__iter_challenges():
            yield Challenge(
                ctf=self,
                name=challenge["name"],
                category=challenge["category"],
                description=challenge["description"],
                value=challenge["points"],
                files=list(map(self.__get_file_url, challenge.get("files", []))),
            )


def get_credentials(username=None, password=None):
    username = username or os.environ.get("CTF_USERNAME", input("User/Email: "))
    password = password or os.environ.get(
        "CTF_PASSWORD", getpass("Password: ", stream=None)
    )

    return username, password


CTFs = CaseInsensitiveDict(data={"CTFd": CTFd, "rCTF": rCTF})


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {ver}".format(ver=__version__),
    )

    parser.add_argument("url", help="ctf url (for example: https://demo.ctfd.io/)")
    parser.add_argument(
        "-c", "--ctf-platform", choices=CTFs, help="ctf platform", default="CTFd"
    )
    parser.add_argument(
        "-n", "--no-login", action="store_true", help="login is not needed"
    )
    parser.add_argument("-u", "--username", help="username")
    parser.add_argument("-p", "--password", help="password")
    parser.add_argument("-t", "--token", help="team token for rCTF")
    parser.add_argument("-F", "--force", help="team token for rCTF")
    sys_args = vars(parser.parse_args(args=args))

    # Configure Logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )

    ctf = CTFs.get(sys_args["ctf_platform"])(sys_args["url"])
    if sys_args["ctf_platform"].lower() == "rctf":
        if not ctf.login(sys_args["token"]):
            raise BadTokenException()
    elif not sys_args["no_login"] or not os.environ.get("CTF_NO_LOGIN"):
        if not ctf.login(*get_credentials(sys_args["username"], sys_args["password"])):
            raise BadUserNameOrPasswordException()

    # check available config
    if ctf.load_config() and not sys_args["force"]:
        logging.info("Config file found, updating challenges")
        ctf.update()
        return

    ctf.save()

    if not sys_args["no_login"] or not os.environ.get("CTF_NO_LOGIN"):
        ctf.logout()


if __name__ == "__main__":
    main()
