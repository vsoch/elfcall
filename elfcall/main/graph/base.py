__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys
import os


class GraphBase:
    def __init__(self, target, results, outfile=None):
        self.results = results
        self.uids = {}
        self.symbol_uids = {}
        self.linked_libs = {}
        self.fullpaths = {}
        self.target = target
        self.parse()
        self._outfile = outfile

    @property
    def outfile(self):
        if not self._outfile:
            self._outfile = (
                sys.stdout
            )  # utils.get_tmpfile(prefix="elfcall-", suffix=".txt")
        return self._outfile

    def get_found_imported(self):

        imported = set()

        # filename is the library importing
        for filename, metas in self.organized.items():

            # meta here (lib) is the one exporting e.g., lib -> export -> filename
            for meta in metas:
                symbol = meta["name"]
                typ = meta["type"]
                bind = meta["bind"]
                imported.add((symbol, typ, bind))
        return imported

    def parse(self):
        """
        Organize locations by fullpath and linked libs, and generate placeholder names
        """
        self.organized = {}

        # Create placeholder for the main binary of interest
        self.uids[self.target["name"]] = self.generate_placeholder()

        # And now for linked libs, etc.
        for symbol, meta in self.results.items():
            if meta["lib"]["fullpath"] not in self.organized:
                self.organized[meta["lib"]["fullpath"]] = []
            self.organized[meta["lib"]["fullpath"]].append(meta)
            self.uids[meta["lib"]["fullpath"]] = self.generate_placeholder()
            self.linked_libs[meta["lib"]["fullpath"]] = meta["linked_libs"]

            # We only need fullpaths for linked libs (not from needed) to get fullpath
            basename = os.path.basename(meta["lib"]["fullpath"])
            if (
                basename in self.fullpaths
                and self.fullpaths[basename] != meta["lib"]["fullpath"]
            ):
                logger.warning(
                    "Warning: a library of the same name (and different path) exists, graph output might not be correct."
                )
            self.fullpaths[basename] = meta["lib"]["fullpath"]

        for filename, linked_libs in self.linked_libs.items():
            for linked_lib in linked_libs:
                self.uids[linked_lib] = self.generate_placeholder()

    def generate_placeholder(self):
        """
        Generate a unique placeholder name for a node.
        """
        # Taken from the Python3 documentation:
        # https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
        while True:
            name = "".join(
                secrets.choice(string.ascii_letters) for i in range(8)
            ).lower()
            if name not in self.uids and name not in self.symbol_uids:
                return name
