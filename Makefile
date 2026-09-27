.PHONY: clean install

INSTALL=install

prefix=/usr
exec_prefix=$(prefix)
bindir=$(exec_prefix)/bin

salus-pcap:

clean:

install:
	$(INSTALL) -m 755 -D python/ei413-fire-panel.py $(DESTDIR)$(bindir)/ei413-fire-panel
