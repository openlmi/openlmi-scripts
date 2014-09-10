# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = _build
SRCDIR        = ..
ROOTDIR       = $(dir $(lastword $(MAKEFILE_LIST)))
COMMAND_NAME ?= $(shell basename $$(dirname `pwd`))
# command names that shall be installed together with this one
# in order to generated documentation
REQUIRED_COMMANDS ?=

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: \
    help clean html dirhtml singlehtml epub latex latexpdf cmdline.generated

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  epub       to make an epub"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo " "
	@echo "  cmdregen   to regenerate cmdline.generated with actual content from installed lmi help"

cmdregen: cmdline.generated

cmdline.generated:
	if ! python -c 'import lmi.scripts.$(COMMAND_NAME)' >/dev/null; then \
		echo "Please install the command library first." >&2; \
		exit 1; \
	fi
	( \
	echo ".."; \
	echo "    !!!!!!!!!"; \
	echo -n "    This is generated file. Use 'make cmdregen' to regenerate it"; \
	echo " from installed 'lmi help <CMD_NAME>'"; \
	echo "    !!!!!!!!!"; \
	echo ; \
	for i in `sed -n '/entry_points/,/)/p' $(SRCDIR)/setup.py | \
			sed -n "s/\s*,\?['\"]\s*\([a-z-]\+\)\s*=.*/\1/p"`; do \
		lmi help $$i | python $(ROOTDIR)/tools/help2rst $$i | \
			tr -d '\033' |sed 's/..1034h//';  \
	done \
	) > $@

conf.py: conf.py.skel
	make -C $(SRCDIR) setup

%.build: conf.py
	SPHINXBUILD=$(SPHINXBUILD) SRCDIR=$(SRCDIR) \
	        REQUIRED_COMMANDS=$(REQUIRED_COMMANDS) \
	    $(ROOTDIR)/tools/build-with-sphinx.sh -b $* \
	        $(ALLSPHINXOPTS) $(BUILDDIR)/$*
	@echo "$* build finished. Output is in $(BUILDDIR)/$*."

clean:
	-rm -rf $(BUILDDIR)/*

html dirhtml singlehtml epub latex: %: %.build

latexpdf:       latex
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."
