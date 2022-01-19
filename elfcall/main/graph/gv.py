__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys

from .base import GraphBase


class Gv(GraphBase):
    def generate(self):
        logger.info("Output will be written to %s" % self.outfile)
        with open(self.outfile, "w") as fd:

            # TODO add fontname
            fontname = None

            # TODO need to add endianness here as string and elfclass
            endianstr = "big_endian"  # vs little_endial
            elfclass = "ELFCLASS"
            digraphname = (
                "full_directory_scan_"
                + architecture
                + "_"
                + o
                + "_"
                + endianstr
                + "_"
                + str(elfclass)
            )
            fd.write("digraph " + digraphname + " {\n ratio=0.562;\n")

            # TODO add fontname here
            if fontname is not None:
                for node in ["graph", "node", "edge"]:
                    fd.write(" " + node + ' [fontname="' + fontname + '"];\n')

            newline = "\n"
            for filename, symbols in self.organized.items():
                if seenfirst:
                    fd.write(newline)
                else:
                    seenfirst = True
                fd.write(
                    ' %s [label="%s" tooltip="%s"];'
                    % (
                        self.uids[filename],
                        os.path.basename(filename),
                        filename,
                    )
                )

            # Record linked dependencies
            seenfirst = False
            for filename, symbols in self.organized.items():
                for linked_lib in self.linked_libs[filename]:
                    if seenfirst:
                        fd.write(newline)
                    else:
                        seenfirst = True

                    # This originally had "if forcesymbols"
                    fd.write(
                        ' %s -> %s [label=" links with " tooltip="%s -> %s"];'
                        % (
                            self.uids[filename],
                            self.uids[linked_lib],
                            filename,
                            linked_lib,
                        )
                    )

            exported = self.get_exported()

            # Create a placeholder for each
            for symbol in exported:
                placeholder = self.generate_placeholder()
                self.symbol_uids[symbol[0]] = placeholder
                fd.write(newline)
                fd.write(
                    ' %s [label="%s" tooltip="%s"];'
                    % (
                        placeholder,
                        symbol[0],
                        symbol[1],
                    )
                )

                fd.write(
                    ' %s -> %s [label=" exports " tooltip="%s -> %s (%s)"];'
                    % (
                        self.uids[filename],
                        placeholder,
                        filename,
                        symbol[0],
                        symbol[1],
                    )
                )

            # store which files use which symbols
            for filename, metas in self.organized.items():
                for meta in metas:
                    symbol = meta["name"]
                    placeholder = self.symbol_uids[symbol]
                    fd.write(
                        ' %s -> %s [label=" uses " tooltip="%s -> %s (%s)"];'
                        % (
                            self.uids[filename],
                            placeholder,
                            filename,
                            symbol,
                            meta["tpy"],
                        )
                    )
            fd.write("\n}\n")
