include Makefile.inc

COMMANDS ?= $(shell find commands -mindepth 1 -maxdepth 1 -type d)
# all rules executable on meta-command and commands
RULES := setup upload upload_docs clean
MASSRULES := $(foreach rule,$(RULES),$(rule)-all)

.PHONY: $(MASSRULES)

$(MASSRULES): %-all: %
	# executes rule for metacommand and for all commands found
	for cmd in $(COMMANDS); do \
	    make -C $$cmd $*; \
	done
