# LinChat Makefile

PREFIX ?= /usr/local
BINDIR = $(DESTDIR)$(PREFIX)/bin
DATADIR = $(DESTDIR)$(PREFIX)/share
CONFDIR = $(DESTDIR)/etc/linchat
APPDIR = $(DATADIR)/applications
DOCDIR = $(DATADIR)/doc/linchat

# Colors for terminal output
YELLOW = \033[1;33m
GREEN = \033[1;32m
NC = \033[0m

.PHONY: all install uninstall clean run deps lint package-arch package-deb package update-version

all: run

# Install dependencies
deps:
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	@pip3 install --user -r requirements.txt
	@if [ -f /etc/os-release ] && grep -q "ID=arch" /etc/os-release; then \
		echo "$(YELLOW)Installing Arch Linux specific dependencies...$(NC)"; \
		sudo pacman -S --needed python-gobject gtk3; \
	elif [ -f /etc/os-release ] && grep -q "ID=ubuntu\|ID=debian" /etc/os-release; then \
		echo "$(YELLOW)Installing Debian/Ubuntu specific dependencies...$(NC)"; \
		sudo apt-get install -y python3-gi gir1.2-gtk-3.0; \
	fi
	@echo "$(GREEN)Dependencies installed.$(NC)"

# Run a linting check
lint:
	@echo "$(YELLOW)Linting Python code...$(NC)"
	@if command -v pycodestyle >/dev/null 2>&1; then \
		pycodestyle --ignore=E501 linchat.py; \
	else \
		echo "pycodestyle not found. Skipping lint."; \
		echo "Install with: pip install pycodestyle"; \
	fi

# Run the application
run:
	@echo "$(YELLOW)Running LinChat...$(NC)"
	@python3 linchat.py

# Install the application
install:
	@echo "$(YELLOW)Installing LinChat to $(BINDIR)...$(NC)"
	@mkdir -p $(BINDIR)
	@cp linchat.py $(BINDIR)/linchat
	@chmod 755 $(BINDIR)/linchat

	@echo "$(YELLOW)Installing desktop file...$(NC)"
	@mkdir -p $(APPDIR)
	@cp pkg/arch/linchat.desktop $(APPDIR)/

	@echo "$(YELLOW)Installing configuration files...$(NC)"
	@mkdir -p $(CONFDIR)
	@echo "[API]" > $(CONFDIR)/config.ini.example
	@echo "endpoint = https://api.openai.com/v1/chat/completions" >> $(CONFDIR)/config.ini.example
	@echo "api_key = your_api_key_here" >> $(CONFDIR)/config.ini.example
	@echo "model = gpt-3.5-turbo" >> $(CONFDIR)/config.ini.example

	@echo "$(YELLOW)Installing documentation...$(NC)"
	@mkdir -p $(DOCDIR)
	@cp README.md $(DOCDIR)/
	@cp LICENSE $(DOCDIR)/

	@echo "$(GREEN)Installation complete!$(NC)"
	@echo "Configuration example is at $(CONFDIR)/config.ini.example"
	@echo "Create your own config at ~/.config/linchat/config.ini"

# Uninstall the application
uninstall:
	@echo "$(YELLOW)Uninstalling LinChat...$(NC)"
	@rm -f $(BINDIR)/linchat
	@rm -f $(APPDIR)/linchat.desktop
	@echo "$(GREEN)LinChat has been uninstalled.$(NC)"
	@echo "Note: Configuration files in $(CONFDIR) and ~/.config/linchat have not been removed."

# Clean up build artifacts
clean:
	@echo "$(YELLOW)Cleaning...$(NC)"
	@rm -rf __pycache__/
	@rm -rf build/
	@rm -rf dist/
	@rm -f debian-binary
	@rm -f *.tar.gz
	@rm -f *.deb
	@rm -f *.changes
	@rm -f *.tar.xz
	@echo "$(GREEN)Cleaned!$(NC)"

# Update version number
update-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "$(YELLOW)Error: VERSION parameter is required. Example: make update-version VERSION=0.2.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Updating version to $(VERSION)...$(NC)"
	@sed -i "s/^pkgver=.*/pkgver=$(VERSION)/" pkg/arch/PKGBUILD
	@sed -i "1s/(.*)/($(VERSION)-1) unstable; urgency=medium/" pkg/debian/changelog
	@echo "$(GREEN)Version updated to $(VERSION)!$(NC)"

# Package for Arch Linux
package-arch:
	@echo "$(YELLOW)Building Arch Linux package...$(NC)"
	@mkdir -p build
	@cp -r pkg/arch/* build/
	@cp LICENSE build/
	@cd build && makepkg -f
	@mv build/*.pkg.tar.zst .
	@echo "$(GREEN)Arch Linux package created.$(NC)"

# Package for Debian/Ubuntu
package-deb:
	@echo "$(YELLOW)Building Debian package...$(NC)"
	@mkdir -p build/debian
	@cp -r pkg/debian/* build/debian/
	@cp linchat.py build/
	@cp LICENSE build/
	@cp README.md build/
	@cp -r pkg/debian build/
	@cd build && debuild -us -uc
	@mv *.deb .
	@echo "$(GREEN)Debian package created.$(NC)"

# Build packages for all supported platforms
package: package-arch package-deb
	@echo "$(GREEN)All packages built successfully!$(NC)"