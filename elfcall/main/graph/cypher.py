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
                os.path.basename(self.target["name"]),
                os.path.basename(self.target["name"]),
            )
        )

        # Create elf for main files and those linked to
        seen_libs = set()
        seen_libs.add(self.target["name"])
        for filename, symbols in self.organized.items():
            if os.path.basename(filename) in self.fullpaths:
                filename = self.fullpaths[os.path.basename(filename)]
            if filename not in seen_libs:
                fd.write(
                    "(%s:ELF {name: '%s', label: '%s'}),\n"
                    % (
                        self.uids[filename],
                        os.path.basename(filename),
                        os.path.basename(filename),
                    )
                )
                seen_libs.add(filename)

            # Now Record linked dependencies
            for linked_lib in self.linked_libs[filename]:

                # linked_libs often are just the basename, but we don't want to add twice
                # so we store the fullpaths here to resolve to fullpath
                if linked_lib in self.fullpaths:
                    linked_lib = self.fullpaths[linked_lib]
                if linked_lib in seen_libs:
                    continue
                seen_libs.add(linked_lib)
                fd.write(
                    "(%s:ELF {name: '%s', label: '%s'}),\n"
                    % (
                        self.uids[linked_lib],
                        os.path.basename(linked_lib),
                        os.path.basename(linked_lib),
                    )
                )
                seen_libs.add(linked_lib)

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
                if linked_lib in self.fullpaths:
                    linked_lib = self.fullpaths[linked_lib]
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
