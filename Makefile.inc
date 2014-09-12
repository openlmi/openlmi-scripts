SELFDIR    := $(dir $(lastword $(MAKEFILE_LIST)))
PYTHONPATH ?= $(HOME)/workspace/python_sandbox
DEVELOPDIR ?= $(shell echo $(PYTHONPATH) | cut -d : -f 1)
VERSION    ?= $(shell cat $(SELFDIR)/VERSION)
# these can be used only after the setup.py is created
EGGNAME     = $(shell python setup.py --name)
SRCDIST     = $(EGGNAME)-$(VERSION).tar.gz

.PHONY: readme sdist develop upload-docs clean all doc setup help

help:
	@echo "Please use \`make <target>' where target is one of:"
	@echo "  setup           Write setup.py script from template."
	@echo "  doc             Build html documentation."
	@echo "  sdist           Create source tarball."
	@echo "  upload          Upload command as a python eggs to PyPI."
	@echo "  upload-docs     Upload commands' documentation to pythonhosted.org."
	@echo "  clean           Remove all temporary files."
	@echo "  develop         Install commands into DEVELOPDIR which defaults"
	@echo "                  to PYTHONPATH. If PYTHONPATH is unset, defaults to"
	@echo "                  '/workspace/python_sandbox'"

setup: setup.py doc/conf.py

%.py: %.py.skel $(SELFDIR)/VERSION
	sed 's/@@VERSION@@/$(VERSION)/g' <$*.py.skel >$@

sdist: setup .$(VERSION).sdist

.$(VERSION).sdist:
	python setup.py sdist
	touch $@

develop: setup
	python setup.py develop --install-dir=$(DEVELOPDIR)

readme: README.txt

%.txt: %.md
	pandoc --from=markdown --to=rst -o $@ $?

doc: setup
	make -C doc html

upload: setup .$(VERSION).upload

.$(VERSION).upload:
	python setup.py sdist upload
	touch $@

upload-docs: setup .$(VERSION).upload_docs

.$(VERSION).upload-docs:
	make -C doc html
	python setup.py upload_docs
	touch $@

clean:
	-rm README.txt setup.py doc/conf.py .$(VERSION).*
	-rm -rf dist/
	make -C doc clean

# ex: ft=make noet sw=8 ts=8
