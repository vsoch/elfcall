.. _getting_started-background:

==========
Background
==========

I found these related libraries:

 - `libtree <https://github.com/haampie/libtree>`_ which I couldn't easily go off of because I'm not an expert in C or C++.
 - `callgraph <https://git.osadl.org/ckresse/callgraph>`_ inspired me for the graphs, but I wanted a slightly more organized implementation.

And wasn't happy that there wasn't at least a high level description of what is going on.
I was also less interested in the graph generation, and more interested in the content of the graph for export or use
elsewhere. I also found the UI interaction to be confusing and wanted to refactor.
Thus, elfcall was a weekend project that would also be useful for my current role,
and I decided to run with it. Elfcall is a combination of "ELF" and then "callgraph."
For this document, I found these documents to be hugely helpful:

 - `manpages for ld <https://man7.org/linux/man-pages/man8/ld.so.8.html>`_
 - `Linuxbase refspecs <https://refspecs.linuxbase.org/elf/gabi4+/ch5.dynamic.html>`_
 - `How to Write Shared Libraries <https://akkadia.org/drepper/dsohowto.pdf>`_
 
Note that I haven't fully gone through the last link yet, and likely this document will be updated as I learn more!

Concepts
========

---
Elf
---

Elf means the "Executable and Linkable Format" and it's the most widely used format of binary on Linux (at least for the time being).
When you run an ELF executable, you are allowed to perform what is called
"dynamic linking" - or finding other libraries at run time to create your final executable program.


---------------
Dynamic Linking
---------------

The basic idea behind dynamic linking is that other libraries might have functions we want to use.
Instead of redundantly including them in our binary, we can link to them. This means that we can reduce
the amount of memory we need to use, more easily upgrade programs that use a specific library,
and overall use less disk space. But in terms of an application binary interface, it does mean
that we can lead to hairy issues if, for example, the binary interface changes between
two versions of a linked library. Don't do that.


How does the process work?
--------------------------

On a high level we:

1. Figure out symbols that are needed (undefined) for a binary of interest.
2. Start parsing the NEEDED libraries in the binary ELF header to look for the symbols.
3. Recursively look for symbols that the library needs.

It's the job of the dynamic linked to start with this list of needed libraries and
search across the system to find contenders and symbols. This is pretty high levle, so
I wanted to write at least a stepwise understanding of what is going on.

1. Choosing a Binary of Interest
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We first choose a binary of interest. It can be a library (``libfoo.so``) or an executable (``/usr/bin/vim``).


2. Verify ELF
^^^^^^^^^^^^^

We then read in our binary and check that it's ELF. This is fairly easy to do and there are different parsers for different languages. For Python there is `pyelftools <https://github.com/eliben/pyelftools>`_ used here, and `debug/elf <https://pkg.go.dev/debug/elf>`_ in golang, which I used in `gosmeagle <https://github.com/vsoch/gosmeagle>`_.
For dynamic linking to work, the ELF needs to have a `dynamic section <https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-42444.html>`_ so we check for that.
I suspect if you provide ``-static`` at compile time, you won't have this dynamic section. From ld's man page:

    Linux binaries require dynamic linking (linking at run time) unless the -static option was given to ld(1) during compilation.

3. Undefined Symbols
^^^^^^^^^^^^^^^^^^^^

If you are just generating a search tree, you can probably skip this step. But for the most part you need to find undefined symbols, where the type is ``UND``.
This typically means that the symbol needs to be provided by a linked library. To find symbols, you can iterate through the ELF sections,
and find the `Symbol Table <https://docs.oracle.com/cd/E23824_01/html/819-0690/chapter6-79797.html>`_ section. For each symbol (per the documentation) you can
find a size, a type, binding, and other metadata. For the most part for other projects I've been interested in the function type (``STT_FUNC``) and object (``STT_OBJ``)
but I don't do special filtering to eliminate them here.


3. Prepare to Parse NEEDED
^^^^^^^^^^^^^^^^^^^^^^^^^^

Our task is to find all the symbols that the library needs. They are going to be found in dependencies that are known via the ELF header.
So we then start with the needed dependencies ``DT_NEEDED`` from the binary of interest's header (a list of library names) 
and add them to a list of lists, let's call this ``needed_search``. We will pop off the first list and continue in a breadth first fashion, 
looking at the original binary needed before we look at any found libraries needed dependencies. 
However, we also honor ``LD_PRELOAD`` in the environment, so if paths are found there first (that exist) we parse them first, and fully (e.g., their needed get parsed before the main binary).
This might be a bug in my implementation if their needed should not be parsed. However, we only allow paths in default search directories (the same as defaults) and in secure mode,
we ignore paths with slashes:

    In secure-execution mode, preload pathnames containing
    slashes are ignored.  Furthermore, shared objects are
    preloaded only from the standard search directories and
    only if they have set-user-ID mode bit enabled (which is
    not typical).

I am checking that, given we have secure mode and an existing path, if set-user-ID mode is enabled but not for the binary, we skip it.
The overall process of parsing NEEDED can be done recursively, or by appending a new list to a list of lists, and continuing until you have an empty list. See `this part <https://github.com/vsoch/elfcall/blob/076b6586c8fdf6a3de77ba099c42150e002d944f/elfcall/main/client.py#L102>`_ of the code for an example. If a dependency is found to have a slash in the path, it's 
used as vertabim. In my script I check to see if it exists first, but the manpages of ld don't state this explicitly:

    When resolving shared object dependencies, the dynamic linker
    first inspects each dependency string to see if it contains a
    slash (this can occur if a shared object pathname containing
    slashes was specified at link time).  If a slash is found, then
    the dependency string is interpreted as a (relative or absolute)
    pathname, and the shared object is loaded using that pathname.

 - While we do this, we keep track of a set of seen names, which should be either the soname, or if the soname is not defined, the library name from the needed header. As we proceed, if we hit a library that we've seen before, we don't search it again. This also prevents us from looping!
 - Implementation wise, this means the first call to the function will find that ``needed_search`` is None (or similar) and we set it to be a the main binary list of needed names inside of a list. Otherwise, we just append the new library we are searching 's needed to the current list of ``needed_search``.

4. Library Search Paths
^^^^^^^^^^^^^^^^^^^^^^^

For each path we find in needed, we first check if we've seen it before (it's in the set of seen) and if so, we continue and skip it.
Given a library name, we then perform a search for the library, and this has a very specific algorithm too that are specific to the ELF we are searching for.

 - Case 1: If we have a ``DT_RPATH`` and ``DT_RUNPATH``, search paths include:
   - ``LD_LIBRARY_PATH``
   - Parsed runpath
   - ld configuration file paths
   - default paths as determined by the system / ABI
 - Case 2: If we only have ``DT_RPATH`` search paths include:
   - Parsed rpath
   - ``LD_LIBRARY_PATH``
   - ld configuration file paths
   - default paths as determined by the system / ABI
 - Case 3: If we only have ``DT_RUNPATH`` search pathsare the same as case 1.

Note that this is for Linux and I'm aware of variation with, for example, musl.
Also note that according to the ld manpages:

    Use of DT_RPATH is deprecated.


So I suspect it's rare to see, but the dynamic linker will still respect it if found.
Also note that ``LD_LIBRARY_PATH`` is not followed given secure execution mode:

    unless the executable is being run in secure-execution mode (see below),
    in which case this variable is ignored.


And we have an added ``--secure`` flag to honor this, if desired. Also note that default paths can also be skipped:


    From the cache file /etc/ld.so.cache, which contains a
    compiled list of candidate shared objects previously found in
    the augmented library path.  If, however, the binary was
    linked with the -z nodeflib linker option, shared objects in
    the default paths are skipped.  Shared objects installed in
    hardware capability directories (see below) are preferred to
    other shared objects.


This can be emulated in the library with ``--no-default-libs``.
For ``LD_LIBRARY_PATH`` (from the environment) and ``RPATH`` and ``RUNPATH`` from the ELF, you will typically get a set of paths 
separated by colons ``:`` or ``;`` to parse. In the case you see an empty entry, e.g., "/path/A:" that typically indicates adding the 
present working directory. As far as I understand, the colon and semicolon are interchangeable. From the ld conf manpages:


        The items in the list are separated by
        either colons or semicolons, and there is no support for
        escaping either separator.  A zero-length directory name
        indicates the current working directory.


For the configuration files, we first look for either ``/etc/ld.so.conf`` and ``/etc/ld-elf.so.conf`` and for each that we find,
we parse the config file. Parsing means:

1. Reading the file line by line (split by newline)
2. Skip empty lines and those that start with ``#`` (comments)
3. If the line starts with include, this is providing another configuration pattern to parse. Remove the "include" and then parse the remaining patter. In Python I use ``glob.glob`` to get the actual files matching the path or pattern. For each file, recursively call the same function to parse it.
4. If you get to the end of the loop and you haven't hit one of the above cases, the line has a library path (append it to your main list)
5. I also keep a lookup of which config file a library came from so I can report it with the tree (not required).

For the above, you can `see the function here <https://github.com/vsoch/elfcall/blob/076b6586c8fdf6a3de77ba099c42150e002d944f/elfcall/main/ld.py#L38>`_.
For default paths, I have hard coded the following for linux:

 - /lib
 - /lib64
 - /usr/lib
 - usr/lib64

For all of the above, the paths you search are going to depend on the ELF you are parsing (e.g., first the original binary of interest, and then a library that you find from it).

**Note I'm still looking into details here! For example, do we need to parse dynamic string tokens?**

5. Find Libraries
^^^^^^^^^^^^^^^^^

Once you have your search paths, our goal is to find the library we are looking for! There are likely a few derivations of how you can do this,
of course with some rules required no matter what, and here is what I did.

1. Any time we find a library, we keep a cache or lookup of the path based on the soname. If the library doesn't have a soname, we use the path. This means that later in the search we won't search for the same thing again. It also means if you have the same soname for different libraries, you aren't going to see the second one.
2. We first look in the library cache to see if we've already found the soname. If yes, we return the associated path. I also return the source (from my source cache) and if we've seen it before (a boolean). E.g., returning at this point would be True, and in the higher level search we would not parse the same library again looking for symbols.
3. If we haven't seen it, we then start looping through the search paths as determined in step 4. For this step, I also keep a cache of files found in search directories, in the case that we've seen one before. if not, I parse the directory.
4. Directory parsing is what you'd expect - we do an os.walk to assemble full paths, exclude broken links, resolve symbolic links, and filter to only include files. One thing I'm not sure about is if we can have repeated libraries of the same basename. This might be a bug in my implementation, but I only include the first found basename, and remember the realpath and fullpath. Note that this might need rethinking and be an edge case of finding the same library (with the same name) in two places and truly wanting to use both.
5. Once we have a listing of files, we "test" each one by loading into ELF. We skip anything that isn't elf.
6. Finally, we do a match to the original binary. Along with needing to find an ELF magic number (the first 4 bytes, which is usually handled by the wrapper library like pyelftools), we need to check header values for each of ``EI_CLASS`` and ``EI_DATA`` (the next 2 bytes that need to match the binary exactly) and then ``EI_ABIVERSION`` and ``EI_OSABI``. For the last one, although it technically needs to be checked, it looks like `there are some deprecations and possible bugs <https://twitter.com/stabbbles/status/1486107888212975616>`_ so I'm not checking it for now.
7. I'm not sure about these yet, but I am also checing ``e_machine``, ``e_type``, ``e_flags``, and ``e_version`` for equality. If they are different (and don't match) we skip.
7. Finally, once we have a definitive library from the path that indeed is a matching ELF, we add its path (by soname) to the library cache. We return the same ELF, path, and False to say that "we haven't seen this one before."

We likely need to look more into how versions are checked because:

        At run time, the dynamic linker
        determines the ABI version of the running kernel and will
        reject loading shared objects that specify minimum ABI
        versions that exceed that ABI version.


If we add this, we might also want to add a variable that "assumes a different kernel"

        LD_ASSUME_KERNEL can be used to cause the dynamic linker
        to assume that it is running on a system with a different
        kernel ABI version.  For example, the following command
        line causes the dynamic linker to assume it is running on
        Linux 2.2.5 when loading the shared objects required by


6. Parse Symbols
^^^^^^^^^^^^^^^^

Back in the main loop, if we have seen the library before, continue and don't parse it again. If we are looking for symbols, then at this point
you want to get symbols that the library exports and compare to the set of imports for the binary in question. You can cross any off the list that are found
and assign them to the library (e.g., I remove from the original list of symbols that need to be found for import and add a record to found symbols,
which includes the path of the library where I found it first. If you are just generating a tree, then you can create some reprsentation of the node,
e.g., I include the level it was found, the source, paths, and name and a space for children:

.. code-block:: python

    # Keep record of what we found!
    node = {
            "level": level,
            "children": [],
            "source": os.path.basename(source),
            "name": os.path.basename(libelf.fullpath),
           }
    node.update({"realpath": libelf.realpath, "fullpath": libelf.fullpath})
    root.append(node)


And then a key is to append the needed libs for the library you found to some list to parse _after_ you are done with this needed set.
That is going to look different depending on ifyou've done this recursively or with some kind of while statement. Ultimately you will
want to call the same search function, but target the "root" node to be the children of each node you just added.


.. code-block:: python

    for next in next_parsed:
        self.recursive_find(
            next["lib"],
            root=next["root"],
            needed_search=next["needed"],
            level=next["level"],
            original=original,
        )


The implementation is really up to you! This is just how I happened to do it.


7. Final Result
^^^^^^^^^^^^^^^

When this recursion or while is finished, you'll either have a nested tree (starting from the root binary) of linked libraries
found, or a similar result but also including symbols. In elftree I can probably improve upon my implementation because I have both
functions (one recursive one not) and use the same functions for both, and this was only because it's more convenient to keep
the list of symbols I'm looking for in one function. But arguably I can refactor to just pass the symbols as an argument in the recursion.
Honestly, I left the non-recursive version because I think it can be easier to understand for some.

**NOTE** I am still adding details to these notes! If you see an issue or want to contribute please open a PR or issue!
