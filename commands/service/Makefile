PYTHONPATH?=$(HOME)/workspace/python_sandbox
DEVELOPDIR?=$(shell echo $(PYTHONPATH) | cut -d : -f 1)

.PHONY: sdist develop upload_docs clean

all: sdist

sdist:
	python setup.py sdist

develop:
	python setup.py develop --install-dir=$(DEVELOPDIR)

upload_docs:
	make -C doc html
	python setup.py upload_docs

clean:
	make -C doc clean
