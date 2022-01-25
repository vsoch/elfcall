#!/usr/bin/env python

__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

import elfcall
from elfcall.logger import setup_logger
import argparse
import sys
import os


def get_parser():
    parser = argparse.ArgumentParser(
        description="Elfcall",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global Variables
    parser.add_argument(
        "--debug",
        dest="debug",
        help="use verbose logging to debug.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--version",
        dest="version",
        help="show software version.",
        default=False,
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        help="actions",
        title="actions",
        description="actions",
        dest="command",
    )

    # The only required argument is some number of binaries to trace
    gen = subparsers.add_parser(
        "gen",
        description="generate the symbol callgraph.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    gen.add_argument(
        "--fmt",
        "-f",
        help="graph format to generate",
        choices=["text", "dot", "gexf", "console", "cypher"],
        default="console",
    )

    tree = subparsers.add_parser(
        "tree",
        description="generate a library tree",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    for command in [gen, tree]:
        command.add_argument("binary", help="binary to scan", nargs=1)
    return parser


def run_client():

    parser = get_parser()

    def help(return_code=0):
        """print help, including the software version and active client
        and exit with return code.
        """

        version = elfcall.__version__

        print("\nSingularity Registry (HPC) Client v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    if args.debug is True:
        os.environ["MESSAGELEVEL"] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version:
        print(elfcall.__version__)
        sys.exit(0)

    setup_logger(
        quiet=args.quiet,
        debug=args.debug,
    )

    # retrieve subparser (with help) from parser
    helper = None
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == args.command:
                helper = subparser
                break

    # Does the user want a shell?
    if args.command == "gen":
        from .gen import main
    elif args.command == "tree":
        from .tree import main

    # Pass on to the correct parser
    return_code = 0
    # try:
    main(args=args, parser=parser, extra=extra, subparser=helper)
    # sys.exit(return_code)
    # except UnboundLocalError:
    #    return_code = 1

    # help(return_code)


if __name__ == "__main__":
    run_client()
