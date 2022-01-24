__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys
import os

from .base import GraphBase


class Dot(GraphBase):
    """
    The dot format is for graphviz
    """

    def generate(self, graphname=None, fontname=None):
        if self.outfile != sys.stdout:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        graphname = graphname or "linked_libs"
        fd.write("digraph " + graphname + " {\n ratio=0.562;\n")

        # Do we want to render using a certain font?
        if fontname is not None:
            for node in ["graph", "node", "edge"]:
                fd.write(" " + node + ' [fontname="' + fontname + '"];\n')

        # Create the main binary and linked libs
        for uid, name, label in self.iter_elf():
            fd.write(' %s [label="%s" tooltip="%s"];\n' % (uid, label, name))

        # Create each symbol
        for uid, name, label, symtype in self.iter_symbols():
            if symtype:
                fd.write(
                    ' %s [label="%s" tooltip="%s (%s)"];\n'
                    % (uid, label, name, symtype)
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
                ' %s -> %s [label=" uses " tooltip="%s -> %s"];\n'
                % (uidfrom, neededuid, filename, needed)
            )

        fd.write("\n}\n")
        if self.outfile != sys.stdout:
            fd.close()
