Documentation
=============
This directory contains usage and developer documentation.
It's available online on [pythonhosted][].

How to build
------------

### Requirements

  * `bash`
  * `GNU make`
  * `setuptools` - provided by package `python-setuptools`
  * `sphinx-build` - provided by package `python-sphinx`

### Steps

    make -C doc html

How to upload
-------------
First build it (see the section above).
Then run:

    python setup.py upload_docs

[pythonhosted]: http://pythonhosted.org/openlmi-scripts/index.html 
