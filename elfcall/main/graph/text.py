__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
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
    def generate(self, include_singles=False):
        if self.outfile != sys.stdout:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        # We don't by default print ELF and SYMBOL (it's redundant)
        if include_singles:

            # Create the main binary and linked libs
            for uid, name, label in self.iter_elf():
                fd.write("{:50} {:20}\n".format("ELF", name))

            # Create each symbol
            for uid, name, label, symtype in self.iter_symbols():
                fd.write("{:50} {:20}\n".format("SYMBOL", name))

        # Links to and from main binary and linked libs
        for fromlib, _, tolib, _ in self.iter_linkswith():
            fd.write("{:50} {:20} {}\n".format(fromlib, "LINKSWITH", tolib))

        # Now add symbols for linked dependences
        for filename, _, symbol, _ in self.iter_exports():
            fd.write("{:50} {:20} {}\n".format(filename, "EXPORTS", symbol))

        # Now add needed by main lib
        for filename, _, symbol, _ in self.iter_needed():
            fd.write("{:50} {:20} {}\n".format(filename, "NEEDS", symbol))

        if self.outfile != sys.stdout:
            fd.close()
