# MCP Security Dynamic Analysis Sandbox
# Based on Ubuntu 22.04 with eBPF/BCC support

FROM ubuntu:22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and BCC tools
RUN apt-get update && apt-get install -y \
    # BCC (BPF Compiler Collection) and eBPF tools
    bpfcc-tools \
    python3-bpfcc \
    libbpfcc \
    linux-headers-generic \
    # Python 3.13 build dependencies
    software-properties-common \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    git \
    # Network tools for debugging
    net-tools \
    iproute2 \
    dnsutils \
    # Process monitoring tools
    procps \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# Install Python 3.13 from deadsnakes PPA
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.13 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.13 1

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Install Python packages (bcc is already available via python3-bpfcc system package)
RUN pip3 install --no-cache-dir \
    docker \
    psutil

# Create directories for monitoring
RUN mkdir -p /target /logs /monitor

# Copy eBPF monitoring scripts
COPY monitors/ebpf_monitor.py /monitor/
COPY monitors/bpf_programs.c /monitor/
COPY monitors/entrypoint.sh /monitor/

# Make entrypoint executable
RUN chmod +x /monitor/entrypoint.sh

# Set working directory
WORKDIR /target

# Entrypoint: Start eBPF monitoring and execute target
ENTRYPOINT ["/monitor/entrypoint.sh"]
