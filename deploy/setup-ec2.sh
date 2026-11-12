#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
    echo "Run this script as the Ubuntu SSH user, not with sudo." >&2
    exit 1
fi

if ! grep -qi ubuntu /etc/os-release; then
    echo "This setup script supports Ubuntu only." >&2
    exit 1
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

source /etc/os-release
ubuntu_codename="${UBUNTU_CODENAME:-${VERSION_CODENAME}}"
architecture="$(dpkg --print-architecture)"
echo "deb [arch=${architecture} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${ubuntu_codename} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker "${USER}"

echo "Docker and the Compose plugin are installed. Log out and back in for docker-group access."
