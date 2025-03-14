# LinChat Packaging

This directory contains packaging files for different Linux distributions.

## Arch Linux

To build the Arch Linux package:

1. Navigate to the `pkg/arch` directory:
   ```bash
   cd pkg/arch
   ```

2. Build the package:
   ```bash
   makepkg -si
   ```

If you want to create a package for the AUR:

1. Update the PKGBUILD with your information
2. Create a `.SRCINFO` file:
   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```
3. Push to the AUR git repository

## Debian/Ubuntu

To build the Debian package:

1. Install build dependencies:
   ```bash
   sudo apt-get install devscripts debhelper dh-python python3-all python3-setuptools
   ```

2. Copy the debian directory to the project root:
   ```bash
   cp -r pkg/debian ./debian
   ```

3. Build the package:
   ```bash
   debuild -us -uc
   ```

4. The .deb package will be created in the parent directory

## Installation from packages

### Arch Linux
```bash
sudo pacman -U linchat-0.1.0-1-any.pkg.tar.zst
```

### Debian/Ubuntu
```bash
sudo dpkg -i linchat_0.1.0-1_all.deb
sudo apt-get install -f  # Install any missing dependencies
```

## Configuration

After installation, create your config file:

```bash
mkdir -p ~/.config/linchat
cp /etc/linchat/config.ini.example ~/.config/linchat/config.ini
```

Then edit the file to add your API key:

```bash
nano ~/.config/linchat/config.ini
```