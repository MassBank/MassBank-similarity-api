FROM mcr.microsoft.com/devcontainers/base:ubuntu26.04

# Java and Maven are required by the OpenAPI Generator launcher in generate.sh.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    default-jre-headless \
    maven \
    vim \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh \
    | env UV_INSTALL_DIR=/usr/local/bin UV_NO_MODIFY_PATH=1 sh

ENV UV_PYTHON_INSTALL_DIR=/usr/local/share/uv/python \
    UV_PYTHON_BIN_DIR=/usr/local/bin \
    UV_LINK_MODE=copy
RUN uv python install --default 3.13 \
    && chmod -R a+rX /usr/local/share/uv

RUN mkdir -p /etc/bash_completion.d \
    && uv generate-shell-completion bash > /etc/bash_completion.d/uv

USER vscode
