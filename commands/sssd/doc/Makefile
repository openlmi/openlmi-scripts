include ../../../Makefile.doc.inc

cmdline.generated:
	if ! python -c 'import lmi.scripts.$(COMMAND_NAME)' >/dev/null; then \
		echo "Please install install the command library first." >&2; \
		exit 1; \
	fi
	( \
	echo ".."; \
	echo ""; \
	echo ".. !!! This is generated file. Use 'make cmdregen' to regenerate it from installed 'lmi help XXX'"; \
	echo ""; \
	echo ; \
	for i in `sed -n '/entry_points/,/)/p' ../setup.py | \
			sed -n "s/\s*,\?['\"]\s*\([a-z-]\+\)\s*=.*/\1/p"`; do \
		lmi help $$i | python ../../../tools/help2rst $$i | \
			tr -d '\033' |sed 's/..1034h//';  \
	done ; \
	for i in domain service; do  \
		lmi help sssd $$i | python ../../../tools/help2rst "sssd $$i" | \
			tr -d '\033' |sed 's/..1034h//';  \
	done \
	) > $@