import json
from urllib.parse import unquote, urljoin

from core.challange import Challenge
from core.ctfs.ctf import CTF


class BadTokenException(Exception):
    pass


class rCTF(CTF):
    def __init__(self, url):
        super().__init__(url)
        self.BarerToken = ""
        self.team_token = ""

    @staticmethod
    def apply_argparser(parser):
        parser.add_argument("-t", "--token", help="team token for rCTF")
        parser.usage += "[-t TEAM_TOKEN] "

    @staticmethod
    def __get_file_url(file_info):
        return file_info["url"]

    def login(self, team_token, no_login=False, **kwargs):
        if no_login:
            return True

        if not team_token:
            team_token = input("Team Token: ")

        team_token = unquote(team_token)
        headers = {"Content-type": "application/json", "Accept": "application/json"}
        res = self.session.post(
            url=urljoin(self.url, "/api/v1/auth/login"),
            headers=headers,
            data=json.dumps({"teamToken": team_token}),
        )

        if not res.ok:
            print(res.status_code)
            print(res.content)
            raise BadTokenException()

        self.BarerToken = json.loads(res.content)["data"]["authToken"]
        self.team_token = team_token

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

    def credential_to_dict(self):
        return {"team_token": self.team_token}

    def credential_from_dict(self, credential):
        self.team_token = credential["team_token"]
