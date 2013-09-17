PYTHONPATH?=$(HOME)/workspace/python_sandbox
DEVELOPDIR?=$(shell echo $(PYTHONPATH) | cut -d : -f 1)

.PHONY: readme sdist develop upload_docs clean all

all: sdist

sdist:
	python setup.py sdist

develop:
	python setup.py develop --install-dir=$(DEVELOPDIR)

readme: README.txt

%.txt: %.md
	pandoc --from=markdown --to=rst -o $@ $?

upload_docs:
	make -C doc html
	python setup.py upload_docs

clean:
	-rm README.txt
	make -C doc clean
