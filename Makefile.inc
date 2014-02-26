SELFDIR    := $(dir $(lastword $(MAKEFILE_LIST)))
PYTHONPATH ?= $(HOME)/workspace/python_sandbox
DEVELOPDIR ?= $(shell echo $(PYTHONPATH) | cut -d : -f 1)
VERSION    ?= $(shell cat $(SELFDIR)/VERSION)
# these can be used only after the setup.py is created
EGGNAME     = $(shell python setup.py --name)
SRCDIST     = $(EGGNAME)-$(VERSION).tar.gz

.PHONY: readme sdist develop upload_docs clean all doc setup

all: sdist

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
	make -C doc

upload: setup .$(VERSION).upload

.$(VERSION).upload:
	python setup.py upload
	touch $@

upload_docs: setup .$(VERSION).upload_docs

.$(VERSION).upload_docs:
	make -C doc html
	python setup.py upload_docs
	touch $@

clean:
	-rm README.txt setup.py .$(VERSION).*
	-rm -rf dist/
	make -C doc clean

# ex: ft=make noet sw=8 ts=8
