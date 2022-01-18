__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

import elfcall.utils as utils
from glob import glob
import os


class LibraryParser:
    def __init__(self):
        """Return a list of parsed paths"""
        self.paths = []

        # Keep lookup of where each came from
        self.sources = []

    def parse(self):
        self.paths += self.parse_ld_so_conf()
        self.paths += self.parse_ld_library_path()
        self.paths += self.set_default_paths()

    def find_source(self, name):
        """
        Given a source directory (usually something from ld paths) return source
        """
        for item in self.sources:
            if item["lib"] == name:
                return item["source"]

    def parse_ld_so_conf(self):
        paths = []
        for filename in ["/etc/ld.so.conf", "/etc/ld-elf.so.conf"]:
            if os.path.exists(filename):
                paths += self._parse_ld_config_file(filename)
        return paths

    def _parse_ld_config_file(self, filename):
        """
        Recursively parse an ld config file
        """
        paths = []
        for line in utils.read_file(filename).split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("include"):
                line = line.replace("include", "").strip()
                for filename in glob(line):
                    paths += self._parse_ld_config_file(filename)
                continue
            # If we get here, append the line
            paths.append(line)

            # Remember where it came from
            self.sources.append({"lib": line, "source": filename})
        return paths

    def parse_ld_library_path(self):
        """
        Get LD_LIBRARY_PATH from the environment
        """
        path = os.environ.get("LD_LIBRARY_PATH")
        if not path:
            return []
        paths = [x for x in path.split(":") if x]
        for path in paths:
            self.sources.append({"lib": path, "source": "LD_LIBRARY_PATH"})
        return paths

    def set_default_paths(self):
        paths = ["/lib", "/lib64", "/usr/lib", "/usr/lib64"]
        for path in paths:
            self.sources.append({"lib": path, "source": "default"})
        return paths
