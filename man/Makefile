BUILDDIR         ?= .
MANPAGE          := lmi.1
TARGET           := $(BUILDDIR)/$(notdir $(MANPAGE)).gz

.PHONY: clean

$(TARGET): $(MANPAGE)
	cat $? | gzip > $@

$(MANPAGE): generate.sh ../config/lmi.conf ../lmi/scripts/_metacommand/toplevel.py
	./generate.sh $@

clean:
	rm -f $(TARGET)
