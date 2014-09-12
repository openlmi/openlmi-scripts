COMMANDS ?= $(notdir $(shell find commands -mindepth 1 -maxdepth 1 -type d))
# all rules executable on meta-command and commands
RULES := setup upload upload-docs clean develop doc
MASSRULES := $(foreach rule,$(RULES),$(rule)-all)

.PHONY: $(MASSRULES) help

help:
	@echo "Please use \`make <target>' where target is one of the following"
	@echo "actions that will be executed on each command:"
	@echo "  setup-all       Write setup.py scripts from templates."
	@echo "  doc-all         Build html documentations."
	@echo "  upload-all      Upload commands as python eggs to PyPI."
	@echo "  upload-docs-all Upload commands' documentation to pythonhosted.org."
	@echo "  clean-all       Remove all temporary files."
	@echo "  develop-all     Install commands into DEVELOPDIR which defaults"
	@echo "                  to PYTHONPATH. If PYTHONPATH is unset, defaults to"
	@echo "                  '/workspace/python_sandbox'"

$(MASSRULES): %-all:
	# executes rule for metacommand and for all commands found
	for cmd in $(COMMANDS); do \
	    make -C commands/$$cmd $*; \
	done
