__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys
from .base import GraphBase


class Console(GraphBase):
    def generate(self):
        for lib, meta in self.organized.items():
            logger.info("==" + lib + "==")
            symbols = [x["name"] for x in meta]
            symbols.sort()
            utils.colify(symbols)


class Text(GraphBase):
    def generate(self):
        if self.outfile != sys.stdout:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        # Record linked dependencies
        for filename, symbols in self.organized.items():
            for linked_lib in self.linked_libs[filename]:
                fd.write("{:50} {:20} {}\n".format(filename, "LINKSWITH", linked_lib))

        # We only care about each library imports (exported from another)
        exported = self.get_exported()

        # Create a placeholder for each
        for symbol in exported:
            placeholder = self.generate_placeholder()
            self.symbol_uids[symbol[0]] = placeholder

        # store which files use which symbols
        for filename, metas in self.organized.items():
            for meta in metas:
                symbol = meta["name"]
                placeholder = self.symbol_uids[symbol]
                fd.write("{:50} {:20} {}\n".format(filename, "EXPORTS", symbol))

        if self.outfile != sys.stdout:
            fd.close()
