import logging
import os
import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from core import __version__
from ctfs import CTFs


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    # Initial parsing to get the platform
    platform = ",".join(CTFs.keys())
    initial_parser = ArgumentParser(
        usage=f"%(prog)s {platform} <url> [-h] [-v] [-n] [-F] [-S LIMITSIZE]",
        formatter_class=ArgumentDefaultsHelpFormatter,
        add_help=False,
    )
    initial_parser.add_argument("ctfs", choices=CTFs.keys(), help="ctf platform")
    initial_args, _ = initial_parser.parse_known_args(args)

    # Add platform-specific arguments
    if CTFs.get(initial_args.ctfs) == None:
        print("Invalid platform")
        initial_parser.print_help()
        exit(1)

    ctfs = CTFs.get(initial_args.ctfs)

    parser = ArgumentParser(
        usage=f"%(prog)s {{{initial_args.ctfs}}} <url> [-h] [-v] [-n] [-F] [-S LIMITSIZE] ",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    ctfs.apply_argparser(parser)

    # Add global arguments
    parser.add_argument("ctfs")
    parser.add_argument("url", help="ctf url (for example: https://demo.ctfd.io/)")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {ver}".format(ver=__version__),
    )
    parser.add_argument(
        "-n", "--no-login", action="store_true", help="login is not needed"
    )
    parser.add_argument(
        "-F", "--force", help="ignore the config file", action="store_true"
    )
    parser.add_argument(
        "-S",
        "--limitsize",
        type=int,
        help="limit size of download file in Mb",
        default=100,
    )

    sys_args = vars(parser.parse_args(args))

    # Configure Logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%d-%m-%y %H:%M:%S",
    )

    ctf = ctfs(sys_args["url"], sys_args["limitsize"], sys_args["force"])
    ctf.login(
        sys_args,
        no_login=(sys_args["no_login"] or os.environ.get("CTF_NO_LOGIN")),
    )

    # check available config
    if ctf.load_config():
        logging.info("Config file found, updating challenges")
        ctf.update()
    else:
        ctf.save()

    if not sys_args["no_login"] or not os.environ.get("CTF_NO_LOGIN"):
        ctf.logout()


if __name__ == "__main__":
    main()
