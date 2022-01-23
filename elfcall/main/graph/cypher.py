__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger

import os
import secrets
import string
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

        # Create the main binary
        fd.write(
            "(%s:ELF {name: '%s', label: '%s'}),\n"
            % (
                self.uids[self.target["name"]],
                self.target["name"],
                os.path.basename(self.target["name"]),
            )
        )

        for filename, symbols in self.organized.items():
            fd.write(
                "(%s:ELF {name: '%s', label: '%s'}),\n"
                % (self.uids[filename], filename, os.path.basename(filename))
            )

        # Found symbols plus needed imported (not necessarily all are found)
        imported = self.get_found_imported()

        # Create a node for each symbol
        seen = set()
        for symbol in imported:
            placeholder = self.generate_placeholder()
            self.symbol_uids[symbol[0]] = placeholder
            fd.write(
                "(%s:SYMBOL {name: '%s', label: '%s', type: '%s'}),\n"
                % (
                    placeholder,
                    symbol[0],
                    symbol[0],
                    symbol[1],
                )
            )
            seen.add(symbol[0])

        # TODO need to fix this so symbols imported have name and type
        for symbol in self.target["imported"]:
            if symbol in seen:
                continue
            placeholder = self.generate_placeholder()
            self.symbol_uids[symbol] = placeholder
            fd.write(
                "(%s:SYMBOL {name: '%s', label: '%s'}),\n"
                % (
                    placeholder,
                    symbol,
                    symbol,
                )
            )

        # First record that each filename links with our main binary
        for filename, symbols in self.organized.items():
            fd.write(
                "(%s)-[:LINKSWITH]->(%s),\n"
                % (
                    self.uids[self.target["name"]],
                    self.uids[filename],
                )
            )

        # Now Record linked dependencies
        for filename, symbols in self.organized.items():
            for linked_lib in self.linked_libs[filename]:
                fd.write(
                    "(%s)-[:LINKSWITH]->(%s),\n"
                    % (
                        self.uids[filename],
                        self.uids[linked_lib],
                    )
                )

        # Now add symbols for linked dependences
        # TODO need to handle last comma...
        for filename, symbols in self.organized.items():
            for symbol in symbols:
                placeholder = self.symbol_uids[symbol["name"]]
                fd.write(
                    "(%s)-[:EXPORTS]->(%s),\n" % (self.uids[filename], placeholder)
                )

        # Now add needed by main lib
        last = len(self.target["imported"]) - 1
        for i, symbol in enumerate(self.target["imported"]):
            placeholder = self.symbol_uids[symbol]
            fd.write(
                "(%s)-[:NEEDS]->(%s)" % (self.uids[self.target["name"]], placeholder)
            )
            if i == last:
                fd.write(";\n")
            else:
                fd.write(",\n")

        if self.outfile != sys.stdout:
            fd.close()


"""            
CREATE (ubbqekvj:ELF {name: '/usr/lib/x86_64-linux-gnu/libstdc++.so.6', label: 'libstdc++.so.6'}),
       (bhtpddun:SYMBOL {name: '__cxa_finalize', label: '__cxa_finalize', type: 'FUNC'}), 
       (jsbdirzz:SYMBOL {name: '_ZNSt8ios_base4InitD1Ev', label: '_ZNSt8ios_base4InitD1Ev', type: 'FUNC'}), 
       (pgrcwngj:SYMBOL {name: '_ZNSt8ios_base4InitC1Ev', label: '_ZNSt8ios_base4InitC1Ev', type: 'FUNC'}), 
       (neuyhhih:SYMBOL {name: '__cxa_atexit', label: '__cxa_atexit', type: 'FUNC'}),
       (ubbqekvj)-[:LINKSWITH]->(vygfepln),
       (ubbqekvj)-[:LINKSWITH]->(luhufmsq),  
       (ubbqekvj)-[:LINKSWITH]->(minajnwv), 
       (ubbqekvj)-[:LINKSWITH]->(xavckaxz), 
       (smajchxe)-[:LINKSWITH]->(minajnwv),
       (smajchxe)-[:EXPORTS]->(bhtpddun),
       (smajchxe)-[:EXPORTS]->(jsbdirzz),
       (smajchxe)-[:EXPORTS]->(neuyhhih),
       (smajchxe)-[:EXPORTS]->(pgrcwngj),
       (ubbqekvj)-[:USES]->(pgrcwngj),
       (ubbqekvj)-[:USES]->(jsbdirzz),
       (smajchxe)-[:USES]->(bhtpddun),
       (smajchxe)-[:USES]->(neuyhhih);
       MATCH (n) RETURN (n)
"""
