# GitHub Workflows for LinChat

This directory contains GitHub Action workflows for automating package releases.

## AUR Publishing (`aur-publish.yml`)

This workflow publishes the package to the Arch User Repository (AUR) when a new GitHub release is created.

### Required Secrets

For the AUR workflow to function, you need to add the following secrets to your GitHub repository:

- `AUR_SSH_PRIVATE_KEY`: Your SSH private key with access to the AUR
- `AUR_USERNAME`: Your AUR username
- `AUR_EMAIL`: The email associated with your AUR account

### How to Set Up AUR Publishing

1. Create an SSH key pair for AUR:
   ```bash
   ssh-keygen -t ed25519 -C "your@email.com" -f ~/.ssh/aur
   ```

2. Add the public key to your AUR account:
   - Go to https://aur.archlinux.org/
   - Log in and go to "My Account"
   - Add the content of `~/.ssh/aur.pub` to "SSH Public Key"

3. Add the private key to GitHub:
   - Go to your repository's Settings > Secrets > Actions
   - Create a new secret named `AUR_SSH_PRIVATE_KEY` with the content of `~/.ssh/aur`
   - Create secrets for `AUR_USERNAME` and `AUR_EMAIL`

4. Create an initial AUR package:
   - Clone the AUR repository: `git clone ssh://aur@aur.archlinux.org/linchat.git`
   - Add your initial files and push

## Launchpad PPA Publishing (`ppa-publish.yml`)

This workflow builds and publishes the package to a Launchpad PPA for Ubuntu when a new GitHub release is created.

### Required Secrets

For the PPA workflow to function, you need to add the following secrets:

- `LAUNCHPAD_GPG_PRIVATE_KEY`: Your exported GPG private key
- `LAUNCHPAD_GPG_PASSPHRASE`: The passphrase for your GPG key
- `LAUNCHPAD_GPG_KEY_ID`: Your GPG key ID
- `LAUNCHPAD_USERNAME`: Your Launchpad username

### How to Set Up PPA Publishing

1. Create a GPG key if you don't have one:
   ```bash
   gpg --gen-key
   ```

2. Export your GPG key:
   ```bash
   gpg --export-secret-keys --armor YOUR_KEY_ID > gpg_private_key.asc
   ```

3. Add the GPG key to Launchpad:
   - Go to https://launchpad.net/~/+editpgpkeys
   - Follow the instructions to add your GPG key

4. Create a PPA on Launchpad if you don't have one:
   - Go to https://launchpad.net/~/+activate-ppa

5. Add the secrets to GitHub:
   - Go to your repository's Settings > Secrets > Actions
   - Add `LAUNCHPAD_GPG_PRIVATE_KEY`, `LAUNCHPAD_GPG_PASSPHRASE`, 
     `LAUNCHPAD_GPG_KEY_ID`, and `LAUNCHPAD_USERNAME`

## Manual Triggering

Both workflows can be triggered manually through the GitHub Actions UI. Go to the Actions tab in your repository, select the workflow, and click "Run workflow".