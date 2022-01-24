__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

from elfcall.logger import logger
import elfcall.main.graph as graph
import elfcall.main.ld as ld
import elfcall.main.elf as elf

from copy import deepcopy
import os


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

        # Cache of sources (e.g., lookup a soname or name and get source path
        self.source_cache = {}

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

        # Load original binary - we need to match elf attributes here
        original = elf.ElfFile(os.path.realpath(binary), binary)
        results = self.recursive_find(binary, original=original)
        self.library_tree(results)

    def recursive_find(
        self, lib, original, root=None, needed_search=None, seen=None, level=0
    ):
        """
        recursively find needed paths, keep track of hierarchy
        """
        # See parse_binary for notes
        e = elf.ElfFile(os.path.realpath(lib), lib)

        # Keep track of libraries we've seen so we don't loop
        if not seen:
            seen = set()

        # If we don't have needed or the root, create data structures
        if root == None and not needed_search:
            root = []
            needed_search = [e.needed]

        # If we have more needed, at to list
        if e.needed:
            needed_search.append(e.needed)

        # Paths to search are defaults plus binary specific
        # DT_RUNPATH/DT_RPATH is searched after LD_LIBRARY_PATH, defaults are last
        search_paths = self.get_search_paths(e)

        # We need to parse next level AFTER so save list
        next_parsed = []

        # First look for libraries in DT_NEEDED on ld.paths
        while needed_search:
            needed = needed_search.pop(0)
            for path in needed:

                # If we've seen something don't go circular
                if path in seen:
                    continue
                seen.add(path)

                # Also pass in original to do matching
                libelf, src, already_seen = self.find_library(
                    path, search_paths, original
                )

                # We might get back a soname instead we've already seen
                if already_seen:
                    continue

                # Assume we must find all libraries (ld paths do not change)
                if not libelf:
                    logger.warning("Cannot find needed library %s" % path)
                    continue

                source = self.ld.find_source(src) or "unknown"

                # Keep record of what we found!
                node = {
                    "level": level,
                    "children": [],
                    "source": os.path.basename(source),
                    "name": os.path.basename(libelf.fullpath),
                }
                node.update({"realpath": libelf.realpath, "fullpath": libelf.fullpath})
                root.append(node)
                if libelf.needed:
                    next_parsed.append(
                        {
                            "lib": libelf.realpath,
                            "root": node["children"],
                            "needed": needed_search,
                            "level": level + 1,
                        }
                    )

        for next in next_parsed:
            self.recursive_find(
                next["lib"],
                root=next["root"],
                needed_search=next["needed"],
                level=next["level"],
                original=original,
            )

        return root

    def library_tree(self, results):
        """
        Generate the library tree
        """

        def parse_result(result):
            spacing = result["level"] * "   "
            # TODO better formatting and color / spacing
            line = spacing + result["name"]
            logger.info(line.ljust(30) + " [" + result["source"] + "]")
            for child in result["children"]:
                parse_result(child)

        for result in results:
            parse_result(result)

    def gen(self, binary=None, fmt=None):
        """
        Generate a graph of symbols (e.g., where everything is found)
        """
        binary = binary or self.binary
        if not binary:
            logger.exit("A binary is required.")
        self.reset()
        self.ld.parse()
        results = self.parse_binary(binary)

        # Results returns locations, imported, and exported
        locations = results["found"]
        binary = {
            "name": binary,
            "exported": results["exported"],
            "imported": results["imported"],
        }

        # Select output format (default to console)
        if fmt == "text":
            out = graph.Text(binary, locations)
        elif fmt == "dot":
            out = graph.Dot(binary, locations)
        elif fmt == "cypher":
            out = graph.Cypher(binary, locations)
        elif fmt == "gexf":
            out = graph.Gexf(binary, locations)
        else:
            out = graph.Console(binary, locations)
        out.generate()

    def get_search_paths(self, e):
        """
        Based on existence of RPATH and RUNTIME path, return ELF search path
        """
        if e.rpath and e.runpath:
            search_paths = (
                self.ld.library_paths
                + e.runpath
                + self.ld.ld.conf_paths
                + self.ld.default_paths
            )
        elif e.rpath:
            search_paths = (
                e.rpath
                + self.ld.library_paths
                + self.ld.conf_paths
                + self.ld.default_paths
            )
        else:
            search_paths = (
                self.ld.library_paths
                + e.runpath
                + self.ld.conf_paths
                + self.ld.default_paths
            )
        return search_paths

    def parse_binary(self, binary):
        """
        Given a binary, figure out how the linker would find symbols
        """
        # https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html# see dynamic-section
        # We first look at symbol table of executive program to find undefined symbols
        # This should fail if not an ELF because we cannot continue
        e = elf.ElfFile(os.path.realpath(binary), binary)

        # Keep track of imported, found imported, and exported
        # imported should be empty at the end
        imported = e.get_imported_symbols()
        exported = e.get_exported_symbols()
        results = {"imported": deepcopy(imported), "exported": exported}
        found = {}

        # Keep track of levels of needed, we will parse through level 0, 1, etc.
        # E.g., needed_search.pop(0) gets the next level to look
        # Same as recursive, but without recursion :)
        search_paths = self.get_search_paths(e)

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

                # This will return loaded ELF, if found, otherwise None
                libelf, _, already_seen = self.find_library(path, search_paths, e)

                # We might get back a soname instead we've already seen
                if already_seen:
                    continue

                # Assume we must find all libraries (ld paths do not change)
                if not libelf:
                    logger.warning("Cannot find needed library %s" % path)
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
                        found[name] = {
                            "lib": {
                                "realpath": libelf.realpath,
                                "fullpath": libelf.fullpath,
                            },
                            "linked_libs": libelf.needed,
                        }
                        found[name].update(symbol)
                        to_removes.append(name)
                for to_remove in to_removes:
                    del imported[to_remove]

                # Break as soon as we find everything needed!
                if not imported:
                    break

        results["found"] = found
        return results

    def find_library(self, name, paths, match_to=None):
        """
        Given a listing of paths, look for a library by name
        """
        logger.debug("Looking for %s" % name)

        # More rare case - the name is a path and it exists
        # If a shared object name has one or more slash (/) characters anywhere in the name
        # the dynamic linker uses that string directly as the path name.
        if os.sep in name and os.path.exists(name):
            self.library_cache[name] = name
            return self.library_cache[name], self.source_cache[name], False

        # We've looked already and found this one before
        if name in self.library_cache:
            return self.library_cache[name], self.source_cache[name], True

        for path in paths:

            # We've already searched this directory
            if path in self.ld_dir_cache:
                files = self.ld_dir_cache[path]

            # Walk the directory to find contender files
            else:
                files = self.parse_dir(path)
                self.ld_dir_cache[path] = files

            if name in files:

                # If we find the library, read ELF and look for symbols
                try:
                    libelf = elf.ElfFile(
                        files[name]["realpath"], files[name]["fullpath"]
                    )
                except:
                    logger.warning("Cannot load %s" % files[name])
                    continue

                # If it does not match the arch and elf type, ignore
                if match_to and not match_to.matches(libelf):
                    continue

                # Here we save based on soname, if defined
                if libelf.soname:
                    self.library_cache[libelf.soname] = libelf
                    self.source_cache[libelf.soname] = path
                    self.source_cache[name] = path
                    return libelf, path, False

                self.library_cache[name] = libelf
                self.source_cache[name] = path
                return libelf, path, False

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
