__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

import os
import re
import stat
from glob import glob

import elfcall.utils as utils


class LibraryParser:
    def __init__(self):
        """Return a list of parsed paths"""
        self._default_lib_paths = ["/lib", "/lib64", "/usr/lib", "/usr/lib64"]
        self.library_paths = []
        self.conf_paths = []

        # Keep lookup of where each came from
        self.sources = []
        self.no_default_libs = False
        self.secure = False

    def parse(self, secure=False, no_default_libs=False):
        """
        Parse paths. We define secure and no default libs here, and arguably
        could support defining it in the init instead.
        """
        self.secure = secure
        self.no_default_libs = no_default_libs
        self.conf_paths = self.parse_ld_so_conf()
        self.library_paths = self.parse_ld_library_path(secure=secure)

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
        # We skip parsing these files if no default paths are used
        if self.no_default_libs:
            return []
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

    def parse_ld_library_path(self, secure=False):
        """
        Get LD_LIBRARY_PATH from the environment
        """
        paths = []
        path = os.environ.get("LD_LIBRARY_PATH")

        # LD_LIBRARY_PATH is used unless the executable is being run in secure-execution mode
        # in which case this variable is ignored.
        if not path or secure:
            return paths
        for path in utils.iter_split_path(path):
            self.sources.append({"lib": path, "source": "LD_LIBRARY_PATH"})
            paths.append(path)
        return paths

    def in_default_path(self, path):
        """
        In secure mode, we only allow a path from ld preload given that it's
        in a default path.
        """
        # I think LD_PRELOAD only loads in default lib search paths?
        # TODO dynamic string tokens can also be expanded here
        regex = re.compile("(%s)" % "|".join(self._default_lib_paths))
        if self.secure and not regex.match(path):
            return False
        return True

    @property
    def ld_preload(self):
        """
        Parse LD_PRELOAD from the environment and (rarely) a system file
        """
        path = os.environ.get("LD_PRELOAD")
        paths = []
        if not path:
            return paths

        for path in utils.iter_split_path(path):

            # In secure-execution mode, preload pathnames containing slashes are ignored
            if self.secure and os.sep in path:
                continue

            # only shared objects in the standard search directories that have the set-user-ID mode bit enabled are loaded.
            if self.secure and os.path.exists(path):

                # It looks like this should be 2048 to be enabled?
                if os.stat(path).st_mode & stat.S_ISUID == 0:
                    continue
            paths.append(path)

        paths += self._parse_ld_so_preload()
        return paths

    def _parse_ld_so_preload(self):
        """
        This gets parsed after LD_PRELOAD environment variable.
        """
        paths = []
        # File containing a whitespace-separated list of ELF shared objects to be loaded before the program.
        if os.path.exists("/etc/ld.so.preload"):
            for line in utils.read_file("/etc/ld.so.preload").split(" "):
                line = line.strip()
                if not line:
                    continue
                paths.append(line)
        return paths

    @property
    def default_paths(self):
        if self.no_default_libs:
            return []
        return self._default_lib_paths

    def set_default_paths(self):
        """
        Add to sources, but don't add to paths list, because default paths
        come after the DT_RUNTIME and/or DT_RPATH.
        """
        for path in self.default_paths:
            self.sources.append({"lib": path, "source": "default"})
        return []
