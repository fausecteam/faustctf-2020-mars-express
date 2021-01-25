SERVICE := mars-express
DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install

build:
	MCC=../movfuscator/build/movcc $(MAKE) -C src

install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)
	cp src/mars-express $(DESTDIR)$(SERVICEDIR)/
	mkdir -p $(DESTDIR)/etc/systemd/system
	cp src/service/mars-express@.service $(DESTDIR)/etc/systemd/system/
	cp src/service/mars-express.socket $(DESTDIR)/etc/systemd/system/
	cp src/service/system-mars-express.slice $(DESTDIR)/etc/systemd/system/
	cp 'src/service/srv-mars\x2dexpress-data.mount' $(DESTDIR)/etc/systemd/system/
