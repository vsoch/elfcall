__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


from elfcall.main import BinaryInterface
from elfcall.logger import logger


def main(args, parser, extra, subparser):

    if not args.binary:
        logger.exit("You must provide one or more binaries to parse.")
    cli = BinaryInterface(args.binary[0], quiet=args.quiet)
    cli.tree()
