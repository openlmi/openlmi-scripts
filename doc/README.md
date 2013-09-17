Documentation
=============
This directory contains usage and developer documentation.
It's available online on [pythonhosted][].

How to build
------------
Supported builds are *html*, *pdflatex* and *epub*.

### Requirements

  * `bash`
  * `GNU make`
  * `setuptools` - provided by package `python-setuptools`
  * `sphinx-build` - provided by package `python-sphinx`

### Steps
There are two kinds of builds available. One containing documentation of `lmi`
command libraries and one with just references to them to external sources.
Following examples will generate only *html* documentation, to make any other
just replace the `html` argument with prefered one.

#### Including commands documentation

    INCLUDE_COMMANDS=1 make -C doc html

#### Without commands documentation
This build is the preferred one for Python Hosted site.

    make -C doc html

How to upload
-------------
First build it (see the section above).
Then run:

    python setup.py upload_docs

[pythonhosted]: http://pythonhosted.org/openlmi-scripts/index.html 
