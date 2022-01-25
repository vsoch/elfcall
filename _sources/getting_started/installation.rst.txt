.. _getting_started-installation:

============
Installation
============

Elfcall can be installed from pypi, or from source. 


Pypi
====

The module is available in pypi as `elfcall <https://pypi.org/project/elfcall/>`_.

.. code:: console

    $ pip install elfcall

This will provide the latest release. If you want a branch or development version, you can install from GitHub, shown next.


Virtual Environment
===================

Here is how to clone the repository and do a local install.

.. code:: console

    $ git clone https://github.com/vsoch/elfcall
    $ cd elfcall

Create a virtual environment (recommended)

.. code:: console

    $ python -m venv env
    $ source env/bin/activate


And then install (this is development mode, remove the -e to not use it)

.. code:: console

    $ pip install -e .

Installation of spliced adds an executable, ``elfcall`` to your path.

.. code:: console

    $ which elfcall
    /opt/conda/bin/elfcall


Once it's installed, you should be able to inspect the client!

.. code-block:: console

    $ elfcall --help


You'll next want to generate a tree or graph, discussed next in :ref:`getting-started`.
