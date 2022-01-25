__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

__version__ = "0.0.0"
AUTHOR = "Vanessa Sochat"
EMAIL = "vsoch@users.noreply.github.io"
NAME = "elfcall"
PACKAGE_URL = "https://github.com/vsoch/elfcall"
KEYWORDS = "ELF, callgraph"
DESCRIPTION = "generate callgraph data for ELF binaries"
LICENSE = "LICENSE"

INSTALL_REQUIRES = (
    ("pyelftools", {"min_version": None}),
    ("jsonschema", {"min_version": None}),
)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES + TESTS_REQUIRES
