__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

from elfcall.logger import logger
import elfcall.main.ld as ld
import elfcall.main.elf as elf
import elfcall.utils as utils

import os
import re
import shutil
import sys


class BinaryInterface:
    """
    Parse binaries to determine symbols needed and interfaces
    """

    def __init__(self, binary=None, quiet=False, skipdirs=None):
        self.quiet = quiet
        self.binary = binary
        self.check()
        self.reset(skipdirs)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[elfcall-binary-interface]"

    def reset(self, skipdirs=None):
        """
        Reset or init attributes
        """
        self.ld = ld.LibraryParser()

        # Cache of directory to files
        self.ld_dir_cache = {}

        # Cache of found library name to path
        self.library_cache = {}

        # Cache of library path to symbols (imported and exported)
        self.symbols_cache = {}

    def check(self):
        """
        Ensure that each binary exists, and we have a fullpath
        """
        if not os.path.exists(self.binary):
            logger.exit("%s does not exist." % self.binary)
        self.binary = os.path.abspath(self.binary)

    def tree(self, binary=None):
        """
        Generate a library tree
        """
        binary = binary or self.binary
        if not binary:
            logger.exit("A binary is required.")
        self.reset()
        self.ld.parse()
        results = self.recursive_find(binary)
        self.library_tree(results)

    def recursive_find(self, lib, root=None, needed_search=None, seen=None, level=0):
        """
        recursively find needed paths, keep track of hierarchy
        """
        # See parse_binary for notes
        e = elf.ElfFile(lib)

        # Keep track of libraries we've seen so we don't loop
        if not seen:
            seen = set()

        # If we don't have needed or the root, create data structures
        if not root and not needed_search:
            root = []
            needed_search = [e.needed]

        # If we have more needed, at to list
        if e.needed:
            needed_search.append(e.needed)

        # First look for libraries in DT_NEEDED on ld.paths
        while needed_search:
            needed = needed_search.pop(0)
            for path in needed:

                # If we've seen something don't go circular
                if path in seen:
                    continue
                seen.add(path)
                lib, src = self.find_library(path, self.ld.paths)

                # Assume we must find all libraries (ld paths do not change)
                if not lib:
                    logger.warning("Cannot find needed library %s" % path)
                    continue

                source = self.ld.find_source(src) or "unknown"
                try:
                    libelf = elf.ElfFile(lib["realpath"])
                except:
                    continue

                # Keep record of what we found!
                node = {
                    "level": level,
                    "children": [],
                    "name": os.path.basename(lib["fullpath"]),
                }
                node.update(lib)
                root.append(node)
                level += 1
                if libelf.needed:
                    self.recursive_find(
                        lib["realpath"],
                        root=node["children"],
                        needed_search=needed_search,
                        seen=seen,
                        level=level,
                    )
        return root

    def library_tree(self, results):
        """
        Generate the library tree
        """

        def parse_result(result):
            spacing = result["level"] * "  "
            logger.info(spacing + result["name"])
            for child in result["children"]:
                parse_result(child)

        for result in results:
            parse_result(result)

    def gen(self, binary=None):
        """
        Generate a graph of symbols (e.g., where everything is found)
        """
        binary = binary or self.binary
        if not binary:
            logger.exit("A binary is required.")
        self.reset()
        self.ld.parse()
        locations = self.parse_binary(binary)

        # Organize locations by fullpath
        organized = {}
        for symbol, meta in locations.items():
            if meta["lib"]["fullpath"] not in organized:
                organized[meta["lib"]["fullpath"]] = []
            organized[meta["lib"]["fullpath"]].append(symbol)

        for lib, symbols in organized.items():
            logger.info("==" + lib + "==")
            symbols.sort()
            utils.colify(symbols)

    def parse_binary(self, binary):
        """
        Given a binary, figure out how the linker would find symbols
        """
        # https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html# see dynamic-section
        # We first look at symbol table of executive program to find undefined symbols
        # This should fail if not an ELF because we cannot continue
        e = elf.ElfFile(binary)

        # Keep track of imported, found imported, and exported
        # imported should be empty at the end
        imported = e.get_imported_symbols()
        exported = e.get_exported_symbols()
        found = {}

        # Keep track of levels of needed, we will parse through level 0, 1, etc.
        # E.g., needed_search.pop(0) gets the next level to look

        # Then at the symbol tables of the DT_NEEDED entries (in order)
        # and then at the second level DT_NEEDED entries, and so on.
        needed_search = [e.needed]

        # Keep track of libraries we've seen
        seen = set()

        # First look for libraries in DT_NEEDED on ld.paths
        while needed_search:
            needed = needed_search.pop(0)
            for path in needed:
                if path in seen:
                    continue
                seen.add(path)
                lib, _ = self.find_library(path, self.ld.paths)

                # Assume we must find all libraries (ld paths do not change)
                if not lib:
                    logger.warning("Cannot find needed library %s" % path)
                    continue

                # If we find the library, read ELF and look for symbols
                try:
                    libelf = elf.ElfFile(lib["realpath"])
                except:
                    continue

                if libelf.needed:
                    needed_search.append(libelf.needed)

                # Did we find any symbols we need?
                exported_contenders = libelf.get_exported_symbols()

                # Keep track of list we found
                to_removes = []
                for name, symbol in imported.items():
                    if name in exported_contenders:
                        logger.debug("Found %s -> %s" % (name, path))
                        found[name] = {"lib": lib}
                        to_removes.append(name)
                for to_remove in to_removes:
                    del imported[to_remove]

                # Break as soon as we find everything needed!
                if not imported:
                    break
        return found

    def find_library(self, name, paths):
        """
        Given a listing of paths, look for a library by name
        """
        logger.debug("Looking for %s" % name)
        # We've looked already and found this first one
        if name in self.library_cache:
            return self.library_cache[name]

        for path in paths:

            # We've already searched this directory
            if path in self.ld_dir_cache:
                files = self.ld_dir_cache[path]

            # Walk the directory to find contender files
            else:
                files = self.parse_dir(path)
                self.ld_dir_cache[path] = files

            if name in files:
                self.library_cache[name] = files[name]
                return self.library_cache[name], path

        return None, None

    def parse_dir(self, path):
        """
        Given a directory path, get all files (fullpaths) in it
        """
        # Lookup of name to fullpath
        libs = {}
        for root, dirs, files in os.walk(path):
            for filename in files:
                fullpath = os.path.join(root, filename)
                if not fullpath:
                    continue

                # Exclude broken links
                if not os.path.exists(fullpath):
                    continue

                # NOTE the link name may be different than first one!
                if os.path.islink(fullpath):
                    realpath = os.path.realpath(fullpath)
                else:
                    realpath = fullpath

                # Ignore anything that isn't a file
                if not os.path.isfile(fullpath):
                    continue

                # Can we have repeated libs? This assumes we only grab the first
                basename = os.path.basename(fullpath)
                if basename not in libs:
                    libs[basename] = {"realpath": realpath, "fullpath": fullpath}

        return libs
