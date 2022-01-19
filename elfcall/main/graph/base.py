__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"


import elfcall.utils as utils
from elfcall.logger import logger
import secrets
import string
import sys


class GraphBase:
    def __init__(self, results, outfile=None, targets=None):
        self.results = results
        self.uids = {}
        self.symbol_uids = {}
        self.linked_libs = {}
        self.parse()
        self.targets = targets or []
        self._outfile = outfile

    @property
    def outfile(self):
        if not self._outfile:
            self._outfile = (
                sys.stdout
            )  # utils.get_tmpfile(prefix="elfcall-", suffix=".txt")
        return self._outfile

    def get_exported(self):

        exported = set()

        # filename is the library importing
        for filename, metas in self.organized.items():

            # meta here (lib) is the one exporting e.g., lib -> export -> filename
            for meta in metas:
                symbol = meta["name"]
                size = meta["size"]
                definition = meta["def"]
                typ = meta["type"]
                bind = meta["bind"]
                exported.add((symbol, typ, bind))
        return exported

    def parse(self):
        """
        Organize locations by fullpath and linked libs, and generate placeholder names
        """
        self.organized = {}
        for symbol, meta in self.results.items():
            if meta["lib"]["fullpath"] not in self.organized:
                self.organized[meta["lib"]["fullpath"]] = []
            self.organized[meta["lib"]["fullpath"]].append(meta)
            self.uids[meta["lib"]["fullpath"]] = self.generate_placeholder()
            self.linked_libs[meta["lib"]["fullpath"]] = meta["linked_libs"]

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
