__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

import elfcall.utils as utils
import elftools.elf.elffile


class ElfFile:
    def __init__(self, realpath, fullpath=None):
        self.realpath = realpath
        self.fullpath = fullpath
        self.dynamic = False

        # We will eventually want imported and exported symbols
        self._exported = {}
        self._imported = {}
        self._needed = []
        self._runpath = []
        self._rpath = []
        self._soname = None

        # Try reading as ELF (will raise exception if fails
        self.fd = open(realpath, "rb")
        self.elf = elftools.elf.elffile.ELFFile(self.fd)
        self.header = self.elf.header

        # We are primarily interested in dynamic elf
        for section in self.elf.iter_sections():
            if isinstance(section, elftools.elf.dynamic.DynamicSection):
                self.dynamicelf = True
                break

    def __exit__(self):
        self.fd.close()

    def yield_tag(self, name):
        for section in self.elf.iter_sections():
            if isinstance(section, elftools.elf.dynamic.DynamicSection):
                for tag in section.iter_tags():
                    if tag.entry.d_tag == name:
                        yield tag

    @property
    def rpath(self):
        if not self._rpath:
            for tag in self.yield_tag("DT_RPATH"):
                if tag.rpath not in self._rpath:
                    self._rpath += utils.iter_splitpath(tag.rpath)
        return self._rpath

    @property
    def runpath(self):
        if not self._runpath:
            for tag in self.yield_tag("DT_RUNPATH"):
                if tag.runpath not in self._runpath:
                    self._runpath += utils.iter_splitpath(tag.runpath)
        return self._runpath

    @property
    def soname(self):
        if not self._soname:
            for tag in self.yield_tag("DT_SONAME"):
                if tag.soname:
                    self._soname = tag.soname
        return self._soname

    @property
    def needed(self):
        if not self._needed:
            for tag in self.yield_tag("DT_NEEDED"):
                if tag.needed not in self._needed:
                    self._needed.append(tag.needed)
        return self._needed

    def matches(self, libelf):
        """
        Compare an elf to another lib's elf type, arch, and header metadata.
        Return True if they match, False otherwise.
        """
        # Note that including EI_OSABI
        # e_ident[EI_DATA], e_ident[EI_CLASS], e_ident[EI_OSABI], e_ident[EI_ABIVERSION],
        for field in ["EI_CLASS", "EI_DATA", "EI_ABIVERSION"]:
            if self.header["e_ident"][field] != libelf.header["e_ident"][field]:
                return False
        # e_machine, e_type, e_flags and e_version.
        for field in ["e_type", "e_machine", "e_flags", "e_version"]:
            if self.header[field] != libelf.header[field]:
                return False
        return True

    @property
    def operating_system(self):
        return self.header["e_ident"]["EI_OSABI"]

    @property
    def arch(self):
        return self.header["e_machine"]

    @property
    def endian(self):
        return self.elf.little_endian

    @property
    def elfcls(self):
        return self.elf.elfclass

    def get_imported_symbols(self):
        if not self._imported:
            self._group_symbols()
        return self._imported

    def get_exported_symbols(self):
        if not self._exported:
            self._group_symbols()
        return self._exported

    def _group_symbols(self):
        """Iterate through symbols and put into imported and exported"""
        for symbol in self.iter_symbols():

            # Strip compiler @@ versions?
            if "@@" in symbol["name"]:
                symbol["name"] = symbol["name"].split("@@")[0]
            if symbol["def"] == "SHN_UNDEF":
                self._imported[symbol["name"]] = symbol
            elif symbol["name"] not in self._exported:
                self._exported[symbol["name"]] = symbol

    def iter_symbols(self):
        for section in self.elf.iter_sections():
            if isinstance(section, elftools.elf.sections.SymbolTableSection):
                for symbol in section.iter_symbols():
                    store = {}
                    if symbol["st_size"] == 0 and symbol["st_shndx"] != "SHN_UNDEF":
                        continue
                    if symbol["st_info"]["type"] == "STT_NOTYPE":
                        continue
                    if symbol["st_info"]["bind"] == "STB_LOCAL":
                        continue
                    if symbol["st_shndx"] == "SHN_ABS":
                        continue

                    # Name and size
                    store["name"] = symbol.name
                    store["size"] = symbol["st_size"]
                    store["def"] = symbol["st_shndx"]

                    # Type
                    if symbol["st_info"]["type"] == "STT_FUNC":
                        store["type"] = "FUNC"
                    elif symbol["st_info"]["type"] == "STT_OBJECT":
                        store["type"] = "OBJECT"
                    elif symbol["st_info"]["type"] == "STT_LOOS":
                        store["type"] = "FUNC"
                    elif symbol["st_info"]["type"] == "STT_TLS":
                        store["type"] = "DATA"

                    if symbol["st_info"]["bind"] == "STB_WEAK":
                        store["bind"] = "WEAK"
                    elif symbol["st_info"]["bind"] == "STB_GLOBAL":
                        store["bind"] = "GLOBAL"
                    yield store
