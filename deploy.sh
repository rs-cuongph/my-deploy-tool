#!/bin/bash

# Deploy Tool - Ubuntu Runner Script
# This script handles dependencies and runs the deployment tool on Ubuntu

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Auto-install Python 3
install_python_auto() {
    print_info "Detecting Linux distribution..."

    # Check if we can use sudo
    if [ "$HAS_SUDO" = false ]; then
        print_error "Python 3 not found and no sudo access for system installation"
        print_info "Please ask your system administrator to install: python3 python3-pip"
        print_info "Or install Python 3 locally using pyenv or conda"
        return 1
    fi

    # Detect package manager and install Python
    if command -v apt &> /dev/null; then
        # Debian/Ubuntu
        print_info "Detected Debian/Ubuntu. Installing Python 3..."
        if sudo apt update && sudo apt install -y python3 python3-pip python3-dev; then
            return 0
        fi
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS/Fedora (older)
        print_info "Detected RHEL/CentOS. Installing Python 3..."
        if sudo yum install -y python3 python3-pip python3-devel; then
            return 0
        fi
    elif command -v dnf &> /dev/null; then
        # Fedora (newer)
        print_info "Detected Fedora. Installing Python 3..."
        if sudo dnf install -y python3 python3-pip python3-devel; then
            return 0
        fi
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        print_info "Detected Arch Linux. Installing Python 3..."
        if sudo pacman -S --noconfirm python python-pip; then
            return 0
        fi
    elif command -v zypper &> /dev/null; then
        # openSUSE
        print_info "Detected openSUSE. Installing Python 3..."
        if sudo zypper install -y python3 python3-pip python3-devel; then
            return 0
        fi
    else
        print_error "Unsupported Linux distribution or package manager not found"
        return 1
    fi

    return 1
}

# Auto-install pip if Python exists but pip doesn't
install_pip_auto() {
    print_info "Installing pip..."

    # Try to install pip using package manager (with sudo)
    if [ "$HAS_SUDO" = true ]; then
        if command -v apt &> /dev/null; then
            # Debian/Ubuntu
            if sudo apt install -y python3-pip; then
                return 0
            fi
        elif command -v yum &> /dev/null; then
            # RHEL/CentOS
            if sudo yum install -y python3-pip; then
                return 0
            fi
        elif command -v dnf &> /dev/null; then
            # Fedora
            if sudo dnf install -y python3-pip; then
                return 0
            fi
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            if sudo pacman -S --noconfirm python-pip; then
                return 0
            fi
        elif command -v zypper &> /dev/null; then
            # openSUSE
            if sudo zypper install -y python3-pip; then
                return 0
            fi
        fi
    fi

    # Fallback: try get-pip.py method (works without sudo)
    print_info "Trying user-level pip installation..."
    if command -v python3 &> /dev/null; then
        if command -v curl &> /dev/null; then
            if curl -s https://bootstrap.pypa.io/get-pip.py | python3 - --user; then
                # Add user pip to PATH for current session
                export PATH="$HOME/.local/bin:$PATH"
                return 0
            fi
        elif command -v wget &> /dev/null; then
            if wget -qO- https://bootstrap.pypa.io/get-pip.py | python3 - --user; then
                # Add user pip to PATH for current session
                export PATH="$HOME/.local/bin:$PATH"
                return 0
            fi
        fi
    fi

    return 1
}

# Check if Python 3 is installed, install if missing
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_success "Python 3 found: $PYTHON_CMD"
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1)
        if [ "$PYTHON_VERSION" = "3" ]; then
            PYTHON_CMD="python"
            print_success "Python 3 found: $PYTHON_CMD"
            return 0
        fi
    fi

    # Python 3 not found, attempt to install
    print_warning "Python 3 not found. Attempting to install..."

    if install_python_auto; then
        # Recheck after installation
        if command -v python3 &> /dev/null; then
            PYTHON_CMD="python3"
            print_success "Python 3 installed successfully: $PYTHON_CMD"
        else
            print_error "Python 3 installation failed"
            exit 1
        fi
    else
        print_error "Failed to install Python 3 automatically"
        print_info "Please install manually: sudo apt update && sudo apt install python3 python3-pip"
        exit 1
    fi
}

# Check if pip is available, install if missing
check_pip() {
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        print_success "pip found: $PIP_CMD"
        return 0
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        print_success "pip found: $PIP_CMD"
        return 0
    fi

    # pip not found, attempt to install
    print_warning "pip not found. Attempting to install..."

    if install_pip_auto; then
        # Recheck after installation
        if command -v pip3 &> /dev/null; then
            PIP_CMD="pip3"
            print_success "pip installed successfully: $PIP_CMD"
        else
            print_error "pip installation failed"
            exit 1
        fi
    else
        print_error "Failed to install pip automatically"
        print_info "Please install manually: sudo apt install python3-pip"
        exit 1
    fi
}

# Install required Python packages
install_dependencies() {
    print_info "Checking Python dependencies..."

    REQUIRED_PACKAGES=(
        "paramiko"
        "scp"
        "pyyaml"
        "tqdm"
        "PySocks"
    )

    MISSING_PACKAGES=()

    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! $PYTHON_CMD -c "import ${package//-/_}" &> /dev/null; then
            MISSING_PACKAGES+=("$package")
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        print_warning "Missing packages: ${MISSING_PACKAGES[*]}"
        print_info "Installing missing packages..."

        for package in "${MISSING_PACKAGES[@]}"; do
            print_info "Installing $package..."
            $PIP_CMD install "$package" --user
        done

        print_success "All dependencies installed"
    else
        print_success "All dependencies are already installed"
    fi
}

# Check if deploy_tool.py exists
check_deploy_tool() {
    if [ ! -f "deploy_tool.py" ]; then
        print_error "deploy_tool.py not found in current directory"
        print_info "Make sure you're running this script from the deployment tool directory"
        exit 1
    fi

    print_success "deploy_tool.py found"
}

# Check if config file exists
check_config() {
    if [ -f "dev.config.yml" ]; then
        print_success "Using development config: dev.config.yml"
        CONFIG_FILE="dev.config.yml"
    elif [ -f "config.yml" ]; then
        print_success "Using production config: config.yml"
        CONFIG_FILE="config.yml"
    else
        print_error "No configuration file found"
        print_info "Create either dev.config.yml or config.yml"
        exit 1
    fi
}

# Check if we have sudo access
check_sudo() {
    if sudo -n true 2>/dev/null; then
        HAS_SUDO=true
        print_info "Sudo access available"
    else
        HAS_SUDO=false
        print_warning "No sudo access. Will try user-level installation only."
    fi
}

# Main execution
main() {
    print_info "Deploy Tool - Ubuntu Runner"
    print_info "=========================="

    # Check sudo access first
    check_sudo

    # Check system requirements
    check_python
    check_pip
    check_deploy_tool
    check_config

    # Install dependencies
    install_dependencies

    print_info "Starting deployment..."
    echo

    # Run the deployment tool with all provided arguments
    $PYTHON_CMD deploy_tool.py "$@"

    DEPLOY_EXIT_CODE=$?

    echo
    if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
        print_success "Deployment completed successfully!"
    else
        print_error "Deployment failed with exit code: $DEPLOY_EXIT_CODE"
        exit $DEPLOY_EXIT_CODE
    fi
}

# Help function
show_help() {
    echo "Deploy Tool - Ubuntu Runner Script"
    echo
    echo "Usage: $0 [OPTIONS] [LOCAL_PATH] [REMOTE_PATH]"
    echo
    echo "This script automatically handles dependencies and runs the deployment tool."
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose logging"
    echo "  --delete       Force delete remote folder before sync"
    echo "  --no-delete    Force disable delete remote folder"
    echo "  -c, --config   Specify configuration file"
    echo
    echo "Examples:"
    echo "  $0                           # Use config file paths"
    echo "  $0 --verbose                 # Run with detailed logging"
    echo "  $0 /local/path /remote/path  # Override config paths"
    echo "  $0 --delete --verbose        # Delete remote folder and show details"
    echo
    echo "Configuration:"
    echo "  - Create dev.config.yml for development"
    echo "  - Create config.yml for production"
    echo "  - Script will auto-detect and use the appropriate config"
    echo
}

# Check for help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Run main function
main "$@"