FROM python:3.10-slim

# Install system packages for a user-friendly dev environment
RUN apt-get update && apt-get install -y \
    bash \
    git \
    curl \
    vim \
    less \
    htop \
    tree \
    ca-certificates \
    locales \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set bash as the default shell
SHELL ["/bin/bash", "-c"]

# Set UTF-8 locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Upgrade pip and install FiftyOne
RUN pip install --upgrade pip setuptools
RUN pip install --no-cache-dir fiftyone

# Download and register FiftyOne plugins
RUN fiftyone plugins download \
    https://github.com/voxel51/fiftyone-plugins \
    --plugin-names @voxel51/plugins

# Custom prompt and colored ls alias
RUN echo "PS1='\\[\\033[1;36m\\]\\u\\[\\033[1;31m\\]@\\[\\033[1;32m\\]\\h:\\[\\033[1;35m\\]\\w\\[\\033[1;31m\\]\\$\\[\\033[0m\\] '" >> /root/.bashrc && \
    echo "alias ls='ls --color=auto'" >> /root/.bashrc

# Set working directory
WORKDIR /workspace
