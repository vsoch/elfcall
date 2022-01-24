__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


from elfcall.logger import logger
import sys

from .base import GraphBase


class Cypher(GraphBase):
    def generate(self):
        if self.outfile == sys.stdout:
            fd = sys.stdout
        else:
            logger.info("Output will be written to %s" % self.outfile)
            fd = open(self.outfile, "w")

        fd.write("CREATE ")

        # Create the main binary and linked libs
        for uid, name, label in self.iter_elf():
            fd.write("(%s:ELF {name: '%s', label: '%s'}),\n" % (uid, name, label))

        # Create each symbol
        for uid, name, label, symtype in self.iter_symbols():
            if symtype:
                fd.write(
                    "(%s:SYMBOL {name: '%s', label: '%s', type: '%s'}),\n"
                    % (uid, name, label, symtype)
                )
            else:
                fd.write(
                    "(%s:SYMBOL {name: '%s', label: '%s'}),\n" % (uid, name, label)
                )

        # Links to and from main binary and linked libs
        for _, uidfrom, _, uidto in self.iter_linkswith():
            fd.write("(%s)-[:LINKSWITH]->(%s),\n" % (uidfrom, uidto))

        # Now add symbols for linked dependences
        for _, uidfile, _, uidsymbol in self.iter_exports():
            fd.write("(%s)-[:EXPORTS]->(%s),\n" % (uidfile, uidsymbol))

        # Now add needed by main lib
        last = len(self.target["imported"]) - 1
        for i, (_, uidfrom, _, neededuid) in enumerate(self.iter_needed()):
            fd.write("(%s)-[:NEEDS]->(%s)" % (uidfrom, neededuid))
            if i == last:
                fd.write(";\n")
            else:
                fd.write(",\n")

        if self.outfile != sys.stdout:
            fd.close()
