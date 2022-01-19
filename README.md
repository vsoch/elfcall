# Elfcall

Generate call graph data for an elf binary.

This works by way of extracting symbols fromthe ELF, figuring out dependencies
via links and RPATH, and then outputting data to file.

Background material about the method can be found in [this article](https://lwn.net/Articles/548216/)
and the [original repository](https://github.com/armijnhemel/conference-talks/tree/master/fsfe2013) and you
can learn more about ELF from any of these sources:

 - https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
 - https://en.wikipedia.org/wiki/Weak_symbol
 - https://refspecs.linuxbase.org/elf/elf.pdf
 - https://android.googlesource.com/platform/art/+/master/runtime/elf.h
 - https://docs.oracle.com/cd/E19683-01/816-1386/chapter6-43405/index.html

And this is helpful for understanding the dynamic linker:

 - https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html#dynamic-section

## Background

I found [callgraph](https://git.osadl.org/ckresse/callgraph) and this seems
like a straight forward way to not just inspect the symbols (undefined, etc.) but to 
see them in the context of which are needed by each library. However, I was less interested
in the graph generation, and more interested in the content of the graph for export or use
elsewhere. I also found the UI interaction to be confusing and wanted to refactor.
Thus, this is an extended version, and per the [original LICENSE](https://git.osadl.org/ckresse/callgraph/-/blob/master/LICENSE)
I am including it here. I needed a different name for pypi because callgraph was
taken, so I am calling it "Elfcall." 

## Usage

### 1. Install

It helps to set up a development environment and then install the library.

```bash
$ python -m venv env
$ pip install -e .
```

### 2. Generate Symbol Graph

The most basic thing you can do is generate:

```bash
cd data/
make
cd ../
```
```bash
$ elfcall gen data/libfoo.so

$ elfcall gen data/libfoo.so
==/usr/lib/x86_64-linux-gnu/libstdc++.so.6==
_ZNSt8ios_base4InitC1Ev    _ZNSt8ios_base4InitD1Ev
==/lib/i386-linux-gnu/libc.so.6==
__cxa_atexit    __cxa_finalize

```

You can add `--debug` to see what is searched and when symbols are found:

```bash
$ elfcall --debug gen data/libfoo.so
Looking for libstdc++.so.6
Found _ZNSt8ios_base4InitC1Ev -> libstdc++.so.6
Found _ZNSt8ios_base4InitD1Ev -> libstdc++.so.6
Looking for libm.so.6
Looking for libgcc_s.so.1
Looking for libc.so.6
Found __cxa_finalize -> libc.so.6
Found __cxa_atexit -> libc.so.6
Looking for ld-linux-x86-64.so.2
Looking for ld-linux.so.2
==/usr/lib/x86_64-linux-gnu/libstdc++.so.6==
_ZNSt8ios_base4InitC1Ev    _ZNSt8ios_base4InitD1Ev
==/lib/i386-linux-gnu/libc.so.6==
__cxa_atexit    __cxa_finalize

```

Note that this is under development, and eventually we will have different graph generation
options (right now we print to the screen).

### 4. Tree

You can also generate a tree of the library paths parsed:

```bash
$ elfcall tree data/libfoo.so
libstdc++.so.6                 [x86_64-linux-gnu.conf]
   libm.so.6                   [i386-linux-gnu.conf]
      libc.so.6                [i386-linux-gnu.conf]
         ld-linux.so.2         [i386-linux-gnu.conf]
      ld-linux-x86-64.so.2     [x86_64-linux-gnu.conf]
      libgcc_s.so.1            [i386-linux-gnu.conf]
```

or:

```bash
$ elfcall tree /usr/bin/vim
libm.so.6                      [i386-linux-gnu.conf]
   ld-linux.so.2               [i386-linux-gnu.conf]
libtinfo.so.6                  [x86_64-linux-gnu.conf]
libselinux.so.1                [x86_64-linux-gnu.conf]
   libpcre2-8.so.0             [x86_64-linux-gnu.conf]
   ld-linux-x86-64.so.2        [x86_64-linux-gnu.conf]
libcanberra.so.0               [x86_64-linux-gnu.conf]
   libvorbisfile.so.3          [x86_64-linux-gnu.conf]
      libvorbis.so.0           [x86_64-linux-gnu.conf]
      libogg.so.0              [x86_64-linux-gnu.conf]
   libtdb.so.1                 [x86_64-linux-gnu.conf]
   libltdl.so.7                [x86_64-linux-gnu.conf]
libacl.so.1                    [x86_64-linux-gnu.conf]
libgpm.so.2                    [x86_64-linux-gnu.conf]
libdl.so.2                     [i386-linux-gnu.conf]
libpython3.8.so.1.0            [x86_64-linux-gnu.conf]
   libexpat.so.1               [x86_64-linux-gnu.conf]
   libz.so.1                   [x86_64-linux-gnu.conf]
   libutil.so.1                [i386-linux-gnu.conf]
libpthread.so.0                [i386-linux-gnu.conf]
libc.so.6                      [i386-linux-gnu.conf]
```

**QUESTION: do we finish parsing level 1 before the others?**

**under development not working yet**

We don't account for symbols here, so if a library is in DT_NEEDED it is searched for.

## License

Licensed under the terms of the General Public License version 3

SPDX-License-Identifier: GPL-3.0-only

Copyright 2018-2019 - Armijn Hemel
Copyright 2021 - Open Source Automation Development Lab (OSADL) eG, author Carsten Emde
Copyright 2022 - Vanessa Sochat (@vsoch)
