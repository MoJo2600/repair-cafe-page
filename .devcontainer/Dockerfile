# Use Python 3.12 on Debian Bookworm as base
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Fix: Remove the broken Yarn repository from the apt sources.
RUN rm -f /etc/apt/sources.list.d/yarn.list

# # Configure apt and install packages
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    build-essential \
    default-mysql-client \
    usbutils \
    libusb-1.0-0 \
    libusb-1.0-0-dev \
    cups-client \
    libjpeg-dev \
    libpng-dev \
    libfreetype-dev \
    libtiff-dev \
    net-tools \
    iproute2 \
    ripgrep \
    vim \
    nano \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS (using NodeSource)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install pnpm and yarn globally
RUN npm install -g pnpm

# Create workspace directory
RUN mkdir -p /workspaces

# Configure CUPS client to use the host CUPS socket (mounted at /run/cups/cups.sock)
RUN mkdir -p /etc/cups \
    && echo "ServerName /run/cups/cups.sock" > /etc/cups/client.conf

# Set up USB device permissions for label printer
# # Create udev rules for USB printers (will need to be activated in privileged mode)
# RUN echo 'SUBSYSTEM=="usb", MODE="0666", GROUP="plugdev"' > /etc/udev/rules.d/99-usb.rules \
#     && echo 'KERNEL=="lp*", MODE="0666", GROUP="lp"' >> /etc/udev/rules.d/99-usb.rules

# Add vscode user to necessary groups for USB/printer access
# RUN usermod -a -G plugdev,lp,dialout vscode 2>/dev/null || true

# Upgrade pip
RUN pip3 install --upgrade pip setuptools wheel

# Install common Python development tools
RUN pip3 install \
    pylint \
    black \
    flake8 \
    mypy \
    pytest \
    ipython

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Set working directory
WORKDIR /workspaces

# Default command
CMD ["sleep", "infinity"]
