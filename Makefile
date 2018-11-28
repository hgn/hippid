MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJ_SRC_PATH := $(notdir $(patsubst %/,%,$(dir $(MKFILE_PATH))))
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
EXEC_DIR := /usr/share/hippo2d
CONF_DIR := /etc/hippo2d


help:
	@echo "install - install distribution to /var/www/hippo2d and systemd unit file"

all:
	help

uninstall:
	@echo "remove runtime data in $(EXEC_DIR)"
	@rm -rf $(EXEC_DIR)
	@if [ -d "$(CONF_DIR)" ] ; \
	then \
		echo "did NOT remove configuration file in $(CONF_DIR) - remove manually if required:" ; \
		echo "e.g. rm -rf $(CONF_DIR)" ; \
	fi
	@echo "uninstallation completed"
	@echo "NOTE: runtime data was NOT deleted"

install:
	@if [ -d "$(EXEC_DIR)" ] ; \
	then \
		echo "$(EXEC_DIR) present, remove first" ; \
		echo "e.g. \"make uninstall\"" ; \
		exit 1 ; \
	fi
	@if [ -d "$(CONF_DIR)" ] ; \
	then \
		echo "$(CONF_DIR) present, did not overwrite convfiguration" ; \
	else \
		echo "create dir $(CONF_DIR)" ; \
		mkdir -p $(CONF_DIR) ; \
		cp $(ROOT_DIR)/assets/hippo2d.conf $(CONF_DIR)/ ; \
	fi
	mkdir -p $(EXEC_DIR)
	cp -r $(ROOT_DIR)/* $(EXEC_DIR)
	cp assets/hippo2d.service /lib/systemd/system/
	chmod 644 /lib/systemd/system/hippo2d.service
	@echo "now call systemctl daemon-reload"
	@echo ".. enable service via: systemctl enable hippo2d"
	@echo ".. start service via: systemctl start hippo2d"
	@echo ".. status via: systemctl status hippo2d"
	@echo ".. logging via: journalctl -u hippo2d"
	@echo ""
	@echo "Don't forget to install required python modules (for root): \"sudo -H pip3 install -r requirements.txt\""
	@echo "and \"sudo apt-get install python3-pip libsasl2-dev pandoc texlive-xetex texlive-latex-extra texlive-latex-recommended libldap-dev\""

ctags:
	ctags -R .
