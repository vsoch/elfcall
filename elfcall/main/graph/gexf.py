__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys

from .base import GraphBase


class Gexf(GraphBase):
    def generate(self):
        logger.info("Output will be written to %s" % self.outfile)
        if self.outfile != sys.stdout:
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        # TODO break this into a text template, don't need lines like this
        fd.write(
            '<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" version="1.2">\n'
        )
        fd.write('    <meta lastmodifieddate="2021-01-01">\n')
        fd.write("        <creator>osadl.org</creator>\n")
        fd.write("        <description>ELF link analysis of</description>\n")
        fd.write("    </meta>\n")
        fd.write('<graph defaultedgetype="directed" idtype="string" type="static">\n')
        fd.write("<nodes>\n")

        seenfirst = False
        for filename, symbols in self.organized.items():
            if seenfirst:
                fd.write("\n")
            else:
                seenfirst = True
                fd.write(
                    '<node id="%s" label="%s"/>'
                    % (
                        self.uids[filename],
                        os.path.basename(filename),
                    )
                )
        fd.write("\n</nodes>")
        fd.write("\n<edges>")

        # Record linked dependencies
        seenfirst = False
        for filename, symbols in self.organized.items():
            for linked_lib in self.linked_libs[filename]:
                if seenfirst:
                    fd.write("\n")
                else:
                    seenfirst = True

                fd.write(
                    '<edge id="%s" source="%s" target="%s" label="links with"/>'
                    % (
                        self.uids[filename] + self.uids[linked_lib],
                        self.uids[filename],
                        self.uids[linked_lib],
                    )
                )
        fd.write("\n</edges>")
        fd.write("\n<nodes>")
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
            fd.write("\n")
            fd.write(
                '<node id="%s" label="%s"/>'
                % (
                    placeholder,
                    symbol[0],
                )
            )

        fd.write("\n</nodes>")
        fd.write("\n<edges>")
        fd.write("\n")

        for symbol in exported:
            placeholder = self.symbol_uids[symbol[0]]
            fd.write(
                '<edge source="%s" target="%s" label="exports"/>'
                % (self.uids[filename], placeholder)
            )

        # store which files use which symbols
        for filename, metas in self.organized.items():
            for meta in metas:
                symbol = meta["name"]
                placeholder = self.symbol_uids[symbol]
                fd.write(
                    '<edge source="%s" target="%s" label="uses"/>'
                    % (
                        self.uids[filename],
                        placeholder,
                    )
                )
        fd.write("\n</edges>")
        fd.write("\n</graph>")
        fd.write("\n</gexf>\n")
        if self.outfile != sys.stdout:
            fd.close()
