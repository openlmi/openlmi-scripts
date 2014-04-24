include ../../../Makefile.doc.inc

cmdline.generated:
	( \
	echo ".."; \
	echo "    !!!!!!!!!"; \
	echo "    This is generated file. Use 'make cmdregen' to regenerate it from installed 'lmi help XXX'"; \
	echo "    !!!!!!!!!"; \
	echo ; \
	lmi help sw | python ../../../tools/help2rst sw | tr -d '\033' |sed 's/..1034h//' ;  \
	for subcmd in `lmi help sw | sed -n "/^Usage:/,/^$$/ s/\s\+lmi sw \([[:alnum:]]\+\).*<args>\.\.\..*/\1/p"`; \
	do \
	    lmi help sw $$subcmd | python ../../../tools/help2rst "sw $$subcmd"; \
	done; \
	) > $@
