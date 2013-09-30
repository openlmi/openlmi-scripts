.PHONY: sdist upload_docs clean

all: sdist

sdist:
	python setup.py sdist

upload_docs:
	make -C doc html
	python setup.py upload_docs

clean:
	make -C doc clean
