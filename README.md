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

The above shows where the undefined symbols in our binary of interest are found.
Note that this isn't a graph, hence why we don't see any kind of entry for the main binary.
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
==/usr/lib/x86_64-linux-gnu/libstdc++.so.6==
_ZNSt8ios_base4InitC1Ev    _ZNSt8ios_base4InitD1Ev
==/lib/x86_64-linux-gnu/libc.so.6==
__cxa_atexit    __cxa_finalize
```

The defaults above show the console. DIfferent formats for graphs are shown below (under development).

#### Text

For text, we will still generate the data as if we are writing nodes and relationships in a graph. This
means we will see what the binary of interest is linked to, and a logical relationship for symbols and libs -
one library will export a symbol, and another will need it.

```bash
$ elfcall gen data/libfoo.so --fmt text
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  LINKSWITH            /usr/lib/x86_64-linux-gnu/libstdc++.so.6
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  LINKSWITH            /lib/x86_64-linux-gnu/libc.so.6
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           LINKSWITH            libm.so.6
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           LINKSWITH            /lib/x86_64-linux-gnu/libc.so.6
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           LINKSWITH            ld-linux-x86-64.so.2
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           LINKSWITH            libgcc_s.so.1
/lib/x86_64-linux-gnu/libc.so.6                    LINKSWITH            ld-linux-x86-64.so.2
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           EXPORTS              _ZNSt8ios_base4InitC1Ev
/usr/lib/x86_64-linux-gnu/libstdc++.so.6           EXPORTS              _ZNSt8ios_base4InitD1Ev
/lib/x86_64-linux-gnu/libc.so.6                    EXPORTS              __cxa_finalize
/lib/x86_64-linux-gnu/libc.so.6                    EXPORTS              __cxa_atexit
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  NEEDS                __cxa_finalize
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  NEEDS                __cxa_atexit
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  NEEDS                _ZNSt8ios_base4InitC1Ev
/home/vanessa/Desktop/Code/elfcall/data/libfoo.so  NEEDS                _ZNSt8ios_base4InitD1Ev
```

For the above, we might be in trouble if the number of `NEEDS` didn't equal the number of `EXPORTS` as we
would be missing a symbol. To pipe to file:

```bash
$ elfcall gen data/libfoo.so --fmt text > data/examples/text/graph.txt
```


#### Cypher

Cypher is the query format for Neo4j, the graph database.

```bash
$ elfcall gen data/libfoo.so --fmt cypher
CREATE (omyaovuh:ELF {name: 'libfoo.so', label: 'libfoo.so'}),
(ilfrbqrc:ELF {name: 'libstdc++.so.6', label: 'libstdc++.so.6'}),
(vyiefgcr:ELF {name: 'libm.so.6', label: 'libm.so.6'}),
(gnxoyhkm:ELF {name: 'libc.so.6', label: 'libc.so.6'}),
(fvynaahi:ELF {name: 'ld-linux-x86-64.so.2', label: 'ld-linux-x86-64.so.2'}),
(hsrlkhie:ELF {name: 'libgcc_s.so.1', label: 'libgcc_s.so.1'}),
(kgyffmqn:SYMBOL {name: '__cxa_finalize', label: '__cxa_finalize', type: 'FUNC'}),
(bieoloch:SYMBOL {name: '_ZNSt8ios_base4InitC1Ev', label: '_ZNSt8ios_base4InitC1Ev', type: 'FUNC'}),
(owpwqsyl:SYMBOL {name: '__cxa_atexit', label: '__cxa_atexit', type: 'FUNC'}),
(stndoxns:SYMBOL {name: '_ZNSt8ios_base4InitD1Ev', label: '_ZNSt8ios_base4InitD1Ev', type: 'FUNC'}),
(omyaovuh)-[:LINKSWITH]->(ilfrbqrc),
(omyaovuh)-[:LINKSWITH]->(lxtmuvsv),
(ilfrbqrc)-[:LINKSWITH]->(vyiefgcr),
(ilfrbqrc)-[:LINKSWITH]->(gnxoyhkm),
(ilfrbqrc)-[:LINKSWITH]->(fvynaahi),
(ilfrbqrc)-[:LINKSWITH]->(hsrlkhie),
(lxtmuvsv)-[:LINKSWITH]->(fvynaahi),
(ilfrbqrc)-[:EXPORTS]->(bieoloch),
(ilfrbqrc)-[:EXPORTS]->(stndoxns),
(lxtmuvsv)-[:EXPORTS]->(kgyffmqn),
(lxtmuvsv)-[:EXPORTS]->(owpwqsyl),
(omyaovuh)-[:NEEDS]->(kgyffmqn),
(omyaovuh)-[:NEEDS]->(owpwqsyl),
(omyaovuh)-[:NEEDS]->(bieoloch),
(omyaovuh)-[:NEEDS]->(stndoxns);
```

Pipe to file:

```bash
$ elfcall gen data/libfoo.so --fmt cypher > data/examples/cypher/graph.cypher
$ elfcall gen /usr/bin/vim --fmt cypher > data/examples/cypher/graph-vim.cypher
```

If you test the output in [https://sandbox.neo4j.com/](https://sandbox.neo4j.com/) by first running the code to generate nodes
and then doing:

```cypher
MATCH (n) RETURN (n)
```

You should see:

![data/examples/cypher/graph.png](data/examples/cypher/graph.png)

Note that this is under development, and eventually we will have different graph generation
options (right now we print to the screen).

#### dot

```bash
$ elfcall gen data/libfoo.so --fmt dot
```

And here is how to generate a png or svg:

```bash
$ elfcall gen data/libfoo.so --fmt dot > data/examples/dot/graph.dot
$ dot -Tpng < data/examples/dot/graph.dot > data/examples/dot/graph.png
```

That generates this beauty!

![https://raw.githubusercontent.com/vsoch/elfcall/main/data/examples/dot/graph.png](https://raw.githubusercontent.com/vsoch/elfcall/main/data/examples/dot/graph.png)

Note that this format isn't great for large graphs.

### 4. Tree

You can also generate a tree of the library paths parsed:

```bash
$ elfcall tree data/libfoo.so
libstdc++.so.6                 [x86_64-linux-gnu.conf]
   ld-linux-x86-64.so.2        [x86_64-linux-gnu.conf]
libm.so.6                      [x86_64-linux-gnu.conf]
libgcc_s.so.1                  [x86_64-linux-gnu.conf]
libc.so.6                      [x86_64-linux-gnu.conf]
```

or:

```bash
$ elfcall tree /usr/bin/vim
libm.so.6                      [x86_64-linux-gnu.conf]
   ld-linux-x86-64.so.2        [x86_64-linux-gnu.conf]
libtinfo.so.6                  [x86_64-linux-gnu.conf]
libselinux.so.1                [x86_64-linux-gnu.conf]
   libpcre2-8.so.0             [x86_64-linux-gnu.conf]
libcanberra.so.0               [x86_64-linux-gnu.conf]
   libvorbisfile.so.3          [x86_64-linux-gnu.conf]
      libvorbis.so.0           [x86_64-linux-gnu.conf]
      libogg.so.0              [x86_64-linux-gnu.conf]
   libtdb.so.1                 [x86_64-linux-gnu.conf]
   libltdl.so.7                [x86_64-linux-gnu.conf]
libacl.so.1                    [x86_64-linux-gnu.conf]
libgpm.so.2                    [x86_64-linux-gnu.conf]
libdl.so.2                     [x86_64-linux-gnu.conf]
libpython3.8.so.1.0            [x86_64-linux-gnu.conf]
   libexpat.so.1               [x86_64-linux-gnu.conf]
   libz.so.1                   [x86_64-linux-gnu.conf]
   libutil.so.1                [x86_64-linux-gnu.conf]
libpthread.so.0                [x86_64-linux-gnu.conf]
libc.so.6                      [x86_64-linux-gnu.conf]
```

## TODO

 - add colors to dot
 - test each of graph generations, add to client
 - logo for library
 - nice documentation
 - tests tests tests!

## License

Licensed under the terms of the General Public License version 3

SPDX-License-Identifier: GPL-3.0-only

Copyright 2018-2019 - Armijn Hemel
Copyright 2021 - Open Source Automation Development Lab (OSADL) eG, author Carsten Emde
Copyright 2022 - Vanessa Sochat (@vsoch)
