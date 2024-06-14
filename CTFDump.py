import logging
import os
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from core import __version__
from core.ctfs import CTFs
from core.ctfs.ctf import load_config


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
    parser.add_argument(
        "-F", "--force", help="ignore the config file", action="store_true"
    )
    sys_args = vars(parser.parse_args(args=args))

    # Configure Logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )

    ctf = CTFs.get(sys_args["ctf_platform"])(sys_args["url"])
    ctf.login(
        username=sys_args["username"],
        password=sys_args["password"],
        team_token=sys_args["token"],
        no_login=(sys_args["no_login"] or os.environ.get("CTF_NO_LOGIN")),
    )

    # check available config
    if load_config() and not sys_args["force"]:
        logging.info("Config file found, updating challenges")
        ctf.update()
    else:
        ctf.save()

    if not sys_args["no_login"] or not os.environ.get("CTF_NO_LOGIN"):
        ctf.logout()


if __name__ == "__main__":
    main()
