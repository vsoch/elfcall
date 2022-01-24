__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys

from datetime import datetime
from .base import GraphBase

template = """<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.1draft" version="1.1" xmlns:viz="http://www.gexf.net/1.1draft/viz" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.1draft http://www.gexf.net/1.1draft/gexf.xsd">
    <meta lastmodifieddate="%s">
        <creator>elfcall</creator>
        <description>ELF link analysis of %s</description>
    </meta>
    <graph defaultedgetype="directed" idtype="string" type="static">
    <nodes>
"""


class Gexf(GraphBase):
    def generate(self):
        if self.outfile != sys.stdout:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")
        else:
            fd = self.outfile

        today = datetime.now().strftime("%Y-%m-%d")

        # Add the binary name and date to the template
        fd.write(template % (today, self.target["name"]))

        # Create the main binary and linked libs
        for uid, name, label in self.iter_elf():
            fd.write('        <node id="%s" label="%s"/>\n' % (uid, name))

        # Create each symbol
        for uid, name, label, symtype in self.iter_symbols():
            fd.write('        <node id="%s" label="%s"/>\n' % (uid, name))
        fd.write("    </nodes>\n")
        fd.write("    <edges>\n")

        # Links to and from main binary and linked libs
        for filename, uidfrom, linked_lib, uidto in self.iter_linkswith():
            edge_uid = uidfrom + uidto
            fd.write(
                '        <edge id="%s" source="%s" target="%s" label="links with"/>\n'
                % (edge_uid, uidfrom, uidto)
            )

        # Now add symbols for linked dependences
        for _, uidfile, _, uidsymbol in self.iter_exports():
            fd.write(
                '        <edge source="%s" target="%s" label="exports"/>\n'
                % (uidfile, uidsymbol)
            )

        # Now add needed by main lib
        for _, uidfrom, _, neededuid in self.iter_needed():
            fd.write(
                '        <edge source="%s" target="%s" label="uses"/>\n'
                % (uidfrom, neededuid)
            )
        fd.write("    </edges>\n")
        fd.write("</graph>\n")
        fd.write("</gexf>\n")

        if self.outfile != sys.stdout:
            fd.close()
