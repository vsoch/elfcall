__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys

from .base import GraphBase


class Cypher(GraphBase):
    def generate(self):
        logger.info("Output will be written to %s" % self.outfile)
        with open(self.outfile, "w") as fd:
            fd.write("CREATE ")
            newline = ", \n"
            seenfirst = False
            for filename, symbols in self.organized.items():
                if seenfirst:
                    fd.write(newline)
                else:
                    seenfirst = True
                    fd.write(
                        "(%s:ELF {name: '%s', label: '%s'})"
                        % (
                            self.uids[filename],
                            filename,
                            os.path.basename(filename),
                        )
                    )

            seenfirst = False
            # Record linked dependencies
            for filename, symbols in self.organized.items():
                for linked_lib in self.linked_libs[filename]:
                    if seenfirst:
                        fd.write(newline)
                    else:
                        seenfirst = True
                    fd.write(
                        "(%s)-[:LINKSWITH]->(%s)"
                        % (
                            self.uids[filename],
                            self.uids[linked_lib],
                        )
                    )

            exported = self.get_exported()

            # Create a placeholder for each
            for symbol in exported:
                placeholder = self.generate_placeholder()
                self.symbol_uids[symbol[0]] = placeholder
                fd.write("\n")
                fd.write(
                    "(%s:SYMBOL {name: '%s', type: '%s'})"
                    % (
                        placeholder,
                        symbol[0],
                        symbol[1],
                    )
                )

                fd.write(newline)
                fd.write("(%s)-[:EXPORTS]->(%s)" % (self.uids[filename], placeholder))

            # store which files use which symbols
            for filename, metas in self.organized.items():
                for meta in metas:
                    symbol = meta["name"]
                    placeholder = self.symbol_uids[symbol]
                    fd.write("(%s)-[:USES]->(%s)" % (self.uids[filename], placeholder))

            fd.write(";\n")
