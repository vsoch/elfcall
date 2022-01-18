__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2022, Vanessa Sochat"
__license__ = "GPL-3.0"

import elftools.elf.elffile


class ElfFile:
    def __init__(self, filename):
        self.filename = filename
        self.dynamic = False

        # We will eventually want imported and exported symbols
        self._exported = {}
        self._imported = {}

        # Try reading as ELF (will raise exception if fails
        self.fd = open(filename, "rb")
        self.elf = elftools.elf.elffile.ELFFile(self.fd)
        self.header = self.elf.header

        # We are primarily interested in dynamic elf
        for section in self.elf.iter_sections():
            if isinstance(section, elftools.elf.dynamic.DynamicSection):
                self.dynamicelf = True
                break

    def __exit__(self):
        self.fd.close()

    @property
    def needed(self):
        linked_libs = []
        for section in self.elf.iter_sections():
            if isinstance(section, elftools.elf.dynamic.DynamicSection):
                for tag in section.iter_tags():
                    if tag.entry.d_tag == "DT_NEEDED" and tag.needed not in linked_libs:
                        linked_libs.append(tag.needed)
        return linked_libs

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
