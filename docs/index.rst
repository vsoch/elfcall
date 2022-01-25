.. _manual-main:

=======
Elfcall
=======

.. image:: https://img.shields.io/github/stars/vsoch/elfcall?style=social
    :alt: GitHub stars
    :target: https://github.com/vsoch/elfcall/stargazers


Generate call graph data for an elf binary.

Elfcall performs two functions:

 - *trees*: generate a tree of libraries akin to what the dynamic linker would see
 - *graphs*: generate a graph that shows linked libraries and symbols exported and needed.
 
For the graphs, there are several different output formats (text, cypher for Neo4j, Dot, and gexf for Gephi or NetworkX).

How does it work?
=================

On a high level, it works by way of extracting symbols from the ELF, and figuring out dependencies
via links and RPATH, and then outputting data to file. An important contribution by way of
developing this library is also trying to document the process, which I found only vaguely
documented in several places. Previous art of interested that inspired me to work on this:

 - `This talk <https://github.com/armijnhemel/conference-talks/blob/master/fsfe2013/fsfe2013.pdf>`_ that gives a good high level overview.
 - `libtree <https://github.com/haampie/libtree>`_ which I couldn't easily go off of because I'm not an expert in C or C++.
 - `callgraph <https://git.osadl.org/ckresse/callgraph>`_ inspired me for the graphs, but I wanted a slightly more organized implementation.

Background material about the method can be found in `this article <https://lwn.net/Articles/548216/>`_
and you can learn more about ELF from any of these sources:

 - https://en.wikipedia.org/wiki/Executable_and_Linkable_Format
 - https://en.wikipedia.org/wiki/Weak_symbol
 - https://refspecs.linuxbase.org/elf/elf.pdf
 - https://android.googlesource.com/platform/art/+/master/runtime/elf.h
 - https://docs.oracle.com/cd/E19683-01/816-1386/chapter6-43405/index.html

And this is helpful for understanding the dynamic linker:

 - https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html#dynamic-section

To see the code, head over to the `repository <https://github.com/vsoch/elfcall/>`_.

.. _main-getting-started:

----------------------------
Getting started with Elfcall
----------------------------

Elfcall can be installed from pypi or directly from the repository. See :ref:`getting_started-installation` for
installation, and then the :ref:`getting-started` section for using elfcall on the command line.

.. _main-support:

-------
Support
-------

* For **bugs and feature requests**, please use the `issue tracker <https://github.com/vsoch/elfcall/issues>`_.
* For **contributions**, visit Spliced on `Github <https://github.com/vsoch/elfcall>`_.

---------
Resources
---------

`GitHub Repository <https://github.com/vsoch/elfcall>`_
    The code on GitHub.


.. toctree::
   :caption: Getting started
   :name: getting_started
   :hidden:
   :maxdepth: 2

   getting_started/index
   getting_started/background
   getting_started/user-guide

.. toctree::
    :caption: API Reference
    :name: api-reference
    :hidden:
    :maxdepth: 1

    api_reference/elfcall
    api_reference/internal/modules
