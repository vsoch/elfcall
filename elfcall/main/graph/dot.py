__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


from elfcall.logger import logger
import random
import sys

from .base import GraphBase


class Dot(GraphBase):
    """
    The dot format is for graphviz
    """

    def generate(self, graphname=None, fontname="Arial"):
        if self.outfile != sys.stdout:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        graphname = graphname or "linked_libs"
        fd.write("digraph " + graphname + " {\n ratio=0.562;\n")

        # Do we want to render using a certain font?
        for node in ["graph", "node", "edge"]:
            fd.write(" " + node + ' [fontname="' + fontname + '"];\n')

        # Color for root (first) and then linked libs, and symbols
        colors = [
            "#" + "".join([random.choice("0123456789ABCDEF") for j in range(6)])
            for i in range(3)
        ]

        root_color = colors.pop()
        linked_color = colors.pop()
        symbol_color = colors.pop()

        # Create the main binary and linked libs
        for i, (uid, name, label) in enumerate(self.iter_elf()):
            if i == 0:
                fd.write(
                    ' %s [label="%s" tooltip="%s", style=filled, color="%s"];\n'
                    % (uid, label, name, root_color)
                )
            else:
                fd.write(
                    ' %s [label="%s" tooltip="%s", style=filled, color="%s"];\n'
                    % (uid, label, name, linked_color)
                )

        # Create each symbol
        for uid, name, label, symtype in self.iter_symbols():
            if symtype:
                fd.write(
                    ' %s [label="%s" tooltip="%s (%s)", style=filled, color="%s"];\n'
                    % (uid, label, name, symtype, symbol_color)
                )
            else:
                fd.write(' %s [label="%s" tooltip="%s"];\n' % (uid, label, name))

        # Links to and from main binary and linked libs
        for filename, uidfrom, linked_lib, uidto in self.iter_linkswith():
            fd.write(
                ' %s -> %s [label=" links with " tooltip="%s -> %s"];\n'
                % (
                    uidfrom,
                    uidto,
                    filename,
                    linked_lib,
                )
            )

        # Now add symbols for linked dependences
        for filename, uidfile, symbol, uidsymbol in self.iter_exports():
            fd.write(
                ' %s -> %s [label=" exports " tooltip="%s -> %s (%s)"];\n'
                % (
                    uidfile,
                    uidsymbol,
                    filename,
                    symbol,
                    uidsymbol,
                )
            )

        # Now add needed by main lib
        for filename, uidfrom, needed, neededuid in self.iter_needed():
            fd.write(
                ' %s -> %s [label=" needs " tooltip="%s -> %s"];\n'
                % (uidfrom, neededuid, filename, needed)
            )

        fd.write("\n}\n")
        if self.outfile != sys.stdout:
            fd.close()
