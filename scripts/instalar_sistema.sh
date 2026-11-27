#!/usr/bin/env bash
# Instala o que precisa de sudo (Debian 13). Rode uma vez: bash scripts/instalar_sistema.sh
set -euo pipefail

echo ">> Instalando Docker e Docker Compose (repositorio oficial do Debian)"
sudo apt-get update
# No Debian 13 o comando `docker` fica no pacote docker-cli, separado do motor (docker.io)
sudo apt-get install -y docker.io docker-cli docker-compose

echo ">> Liberando Docker sem sudo (grupo docker) e a porta USB do ESP32 (grupo dialout)"
sudo usermod -aG docker,dialout "$USER"

sudo systemctl enable --now docker

echo
echo "Pronto. FECHE A SESSAO E ENTRE DE NOVO (ou reinicie) para os grupos valerem."
echo "Depois teste com:  docker run --rm hello-world"
