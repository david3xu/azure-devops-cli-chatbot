FROM mcr.microsoft.com/devcontainers/python:3.8

# Install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    curl \
    wget \
    git \
    gnupg \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    lsb-release

# Install the Azure Developer CLI (azd)
RUN curl -fsSL https://aka.ms/install-azd.sh | bash

# Install jq
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends jq

# Install Bicep CLI
RUN curl -Lo bicep https://github.com/Azure/bicep/releases/latest/download/bicep-linux-x64 \
    && chmod +x ./bicep \
    && mv ./bicep /usr/local/bin/bicep

# Install Azure DevOps CLI extension
RUN az extension add --name azure-devops --yes

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* 