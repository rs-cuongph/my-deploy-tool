#!/bin/bash

# Install Script for Deploy Tool on Ubuntu
# This script sets up the deployment tool with all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system packages
update_system() {
    print_info "Updating system packages..."
    sudo apt update
    print_success "System packages updated"
}

# Install Python and pip if not present
install_python() {
    print_info "Installing Python 3 and pip..."

    # Install Python 3, pip, and development tools
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        build-essential \
        libffi-dev \
        libssl-dev

    print_success "Python 3 and development tools installed"
}

# Install Python packages
install_python_packages() {
    print_info "Installing Python packages..."

    # Install packages globally (you may prefer --user flag)
    pip3 install \
        paramiko \
        scp \
        pyyaml \
        tqdm \
        PySocks

    print_success "Python packages installed"
}

# Make scripts executable
setup_scripts() {
    print_info "Setting up executable scripts..."

    chmod +x deploy.sh
    chmod +x install.sh

    # Create symlink for easier access (optional)
    if [ ! -L "/usr/local/bin/deploy-tool" ]; then
        sudo ln -s "$(pwd)/deploy.sh" /usr/local/bin/deploy-tool
        print_success "Created symlink: deploy-tool command available globally"
    else
        print_info "Global deploy-tool command already exists"
    fi

    print_success "Scripts are now executable"
}

# Create sample config if none exists
create_sample_config() {
    if [ ! -f "dev.config.yml" ] && [ ! -f "config.yml" ]; then
        print_info "Creating sample configuration file..."

        cat > dev.config.yml << 'EOF'
# Development Environment Configuration
paths:
  local: "/path/to/local/source"
  remote: "/path/to/remote/destination"

ssh:
  hostname: "your-server.com"
  port: 22
  username: "your-username"
  password: null  # Use key-based auth if possible
  key_file: "~/.ssh/id_rsa"
  proxy:
    hostname: null  # "proxy-server.com"
    port: null      # 8080
    username: null
    password: null
    type: "http"    # http, socks5, auto

deploy:
  compression: true
  compression_format: "tar.gz"  # tar.gz, zip
  checksum_verify: true
  retry_attempts: 3
  retry_delay: 5  # seconds
  chunk_size: 8192  # bytes for file transfer
  delete_before_sync: false  # Delete remote folder before sync

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "deploy_dev.log"
EOF

        print_warning "Sample config created: dev.config.yml"
        print_info "Please edit the configuration file with your server details"
    else
        print_success "Configuration file already exists"
    fi
}

# Main installation
main() {
    print_info "Deploy Tool Installation for Ubuntu"
    print_info "==================================="

    # Check if running as root for system packages
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This is okay for system package installation."
    fi

    # Run installation steps
    update_system
    install_python
    install_python_packages
    setup_scripts
    create_sample_config

    echo
    print_success "Installation completed!"
    echo
    print_info "Usage:"
    print_info "  ./deploy.sh --help          # Show help"
    print_info "  ./deploy.sh --verbose       # Run deployment with detailed logging"
    print_info "  deploy-tool --verbose       # Use global command (if symlink created)"
    echo
    print_warning "Don't forget to edit your configuration file with real server details!"
}

# Run installation
main "$@"