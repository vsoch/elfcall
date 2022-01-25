.. _getting_started-user-guide:

==========
User Guide
==========



Commands
========

Elfcall provides the following sub-commands via the ``elfcall`` command line client.

Gen
---

Gen is used to generate a symbol graph. This is arguably not going to be the best visualization for
really large trees, however in this case you likely want to use the client to generate
the same graph (we will show both). First, let's combine some example code from
the repository (shown how to clone in :ref:`getting_started-installation`.


.. code-block:: console

    cd data/
    make
    cd ../


This will generate ``data/libfoo.so``, a small library we can use for demonstration.

console
^^^^^^^

The default output prints to the console. Let's run gen and see what happens!


.. code-block:: console

    $ elfcall gen data/libfoo.so


The output is basic in that you will see the linked library followed by undefined symbols we needed.
It's implied that these are needed symbols of ``libfoo.so``.


.. code-block:: console

    $ elfcall gen data/libfoo.so
    ==/usr/lib/x86_64-linux-gnu/libstdc++.so.6==
    _ZNSt8ios_base4InitC1Ev    _ZNSt8ios_base4InitD1Ev
    ==/lib/i386-linux-gnu/libc.so.6==
    __cxa_atexit    __cxa_finalize


The above shows where the undefined symbols in our binary of interest are found.
Note that this isn't a graph, hence why we don't see any kind of entry for the main binary.
You can add ``--debug`` to see what is searched and when symbols are found:


.. code-block:: console

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


This is actually the default output "format" for gen - printing to the console. There
are dIfferent formats for graphs are shown below. To do this same generation in Python:

.. code-block:: python

    from elfcall.main import BinaryInterface
    cli = BinaryInterface("data/libfoo.so")
    
    # These are the same
    cli.gen()
    cli.gen(fmt="console")

    # Instead of printing, get json output
    results = cli.gen_output()


The output "results" will have sets of imported and exported symbols, and then a lookup of what is found
and where. Note that this output is consistent between all graph types, hence why the output format is 
not needed.


text
^^^^

Text output is akin to console, but we are explicitly printing basic entities for a graph.
We are generating the data as if we are writing nodes and relationships in a graph, and (from Python)
there is even an optional boolean to indicate we want to see ELF and SYMBOL entries on their own (default is False). This
means we will see what the binary of interest is linked to, and a logical relationship for symbols and libs -
one library will export a symbol, and another will need it.

.. code-block:: console

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


For the above, we might be in trouble if the number of ``NEEDS`` didn't equal the number of ``EXPORTS`` as we
would be missing a symbol. To pipe to file:


.. code-block:: console

    $ elfcall gen data/libfoo.so --fmt text > data/examples/text/graph.txt

From within Python you might do:


.. code-block:: python

    from elfcall.main import BinaryInterface
    cli = BinaryInterface("data/libfoo.so")    
    cli.gen(fmt="text")


cypher
^^^^^^

Cypher is the query format for Neo4j, the graph database.

.. code-block:: console

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


What you are seeing above is a definition of node and relationships.    
You can pipe to file:


.. code-block:: console

    $ elfcall gen data/libfoo.so --fmt cypher > data/examples/cypher/graph.cypher
    $ elfcall gen /usr/bin/vim --fmt cypher > data/examples/cypher/graph-vim.cypher


If you test the output in `the Neo4J sandbox <https://sandbox.neo4j.com/>`_ by first running the code to generate nodes
and then doing:

.. code-block:: console

    MATCH (n) RETURN (n)


You should see:


.. image:: https://raw.githubusercontent.com/vsoch/elfcall/main/data/examples/cypher/graph.png
  :alt: Cypher Graph


From within Python you might do:

.. code-block:: python

    from elfcall.main import BinaryInterface
    cli = BinaryInterface("data/libfoo.so")    
    cli.gen(fmt="cypher")



dot
^^^

Dot is probably one of my favorite because you can use the `dot <https://linux.die.net/man/1/dot>`_ command line tool to make pretty
beautiful plots!

.. code-block:: console

    $ elfcall gen data/libfoo.so --fmt dot

And here is how to generate a png or svg:

.. code-block:: console

    $ elfcall gen data/libfoo.so --fmt dot > data/examples/dot/graph.dot
    $ dot -Tpng < data/examples/dot/graph.dot > data/examples/dot/graph.png
    $ dot -Tsvg < data/examples/dot/graph.dot > data/examples/dot/graph.svg


That generates this beauty!


.. image:: https://raw.githubusercontent.com/vsoch/elfcall/main/data/examples/dot/graph.png
  :alt: Dot Graph


Note that this format isn't great for large graphs.


Gexf (NetworkX)
^^^^^^^^^^^^^^^

If you want to use networkX or Gephi or `a viewer <https://github.com/raphv/gexf-js>`_ you can generate output as follows:


.. code-block:: console

    $ elfcall gen data/libfoo.so --fmt gexf
    $ elfcall gen data/libfoo.so --fmt gexf > data/examples/gexf/graph.xml


To use the viewer, you'll first need to import into Gephi so the nodes have added
spatial information. Without this information, you won't see them in the UI.
You can then do the following:

.. code-block:: console

    $ here=$PWD
    $ cd /tmp
    $ git clone https://github.com/raphv/gexf-js
    $ cd gexf-js

    # The file we generated above, we copy over the example so we don't have 
    # to edit config.js
    $ cp $here/data/examples/gexf/graph.xml miserables.gexf


And then run the server!


.. code-block:: console
            
    $ python -m http.server 9999


As an alternative, `networkx <https://networkx.org/documentation/stable/tutorial.html>`_ can also read in the gexf file:

.. code-block:: python

    import matplotlib.pyplot as plt
    import networkx as nx

    graph = nx.read_gexf('data/examples/gexf/graph.xml')

    nx.draw(graph, with_labels=True, font_weight='bold')
    plt.show()


Tree
----

Elfcall also lets you generate a tree of the library paths parsed:


.. code-block:: console

    $ elfcall tree data/libfoo.so
    libstdc++.so.6                 [x86_64-linux-gnu.conf]
       ld-linux-x86-64.so.2        [x86_64-linux-gnu.conf]
    libm.so.6                      [x86_64-linux-gnu.conf]
    libgcc_s.so.1                  [x86_64-linux-gnu.conf]
    libc.so.6                      [x86_64-linux-gnu.conf]


Notice the right column, the source of finding a file? This is the source lookup I was talking about in
:ref:`getting_started-background`.


or:

.. code-block:: console

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

