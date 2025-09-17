# Deploy Tool - Ubuntu Setup Guide

A Python-based deployment tool for syncing files to remote servers via SSH with proxy support.

## Quick Start (Ubuntu)

### 1. Installation

```bash
# Clone or download the deployment tool files
# Navigate to the deployment tool directory
cd /path/to/deploy-tool

# Run the installation script
chmod +x install.sh
./install.sh
```

The installation script will:
- Update system packages
- Install Python 3, pip, and development tools
- Install required Python packages (paramiko, scp, pyyaml, tqdm, PySocks)
- Make scripts executable
- Create a global `deploy-tool` command
- Generate a sample configuration file

### 2. Configuration

Edit the configuration file with your server details:

```bash
nano dev.config.yml
```

Example configuration:
```yaml
# Development Environment Configuration
paths:
  local: "/home/user/myproject/dist"
  remote: "/var/www/html"

ssh:
  hostname: "your-server.com"
  port: 22
  username: "deploy-user"
  password: null  # Use key-based auth (recommended)
  key_file: "~/.ssh/id_rsa"
  proxy:
    hostname: "proxy-server.com"  # Optional proxy
    port: 8080
    username: "proxy-user"
    password: "proxy-pass"
    type: "http"  # http, socks5, auto

deploy:
  compression: true
  compression_format: "tar.gz"
  checksum_verify: true
  retry_attempts: 3
  retry_delay: 5
  chunk_size: 8192
  delete_before_sync: false

logging:
  level: "INFO"
  file: "deploy_dev.log"
```

### 3. Usage

```bash
# Basic deployment (uses config file paths)
./deploy.sh

# Verbose deployment with detailed logging
./deploy.sh --verbose

# Override paths from command line
./deploy.sh /local/path /remote/path

# Force delete remote folder before sync
./deploy.sh --delete --verbose

# Use global command (if symlink was created)
deploy-tool --verbose

# Show help
./deploy.sh --help
```

## Manual Installation

If you prefer manual installation:

### Prerequisites

```bash
# Update system
sudo apt update

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-dev build-essential

# Install required Python packages
pip3 install paramiko scp pyyaml tqdm PySocks
```

### Setup

```bash
# Make scripts executable
chmod +x deploy.sh

# Run deployment
./deploy.sh --verbose
```

## Features

- ✅ **Cross-platform**: Works on Windows and Ubuntu
- ✅ **Proxy Support**: HTTP CONNECT and SOCKS5 proxies
- ✅ **Real-time Progress**: Live upload progress with percentage
- ✅ **Compression**: tar.gz or zip compression for faster transfers
- ✅ **Checksum Verification**: Ensures file integrity
- ✅ **Retry Logic**: Automatic retry on connection failures
- ✅ **Flexible Authentication**: Password or key-based SSH auth
- ✅ **Detailed Logging**: Console and file logging with timestamps

## Configuration Options

### SSH Configuration
- `hostname`: Remote server hostname/IP
- `port`: SSH port (default: 22)
- `username`: SSH username
- `password`: SSH password (use `null` for key-based auth)
- `key_file`: Path to SSH private key

### Proxy Configuration
- `hostname`: Proxy server hostname/IP
- `port`: Proxy port
- `username`: Proxy username (if required)
- `password`: Proxy password (if required)
- `type`: Proxy type (`http`, `socks5`, or `auto`)

### Deployment Options
- `compression`: Enable/disable compression
- `compression_format`: `tar.gz` or `zip`
- `checksum_verify`: Verify file integrity
- `retry_attempts`: Number of retry attempts
- `retry_delay`: Delay between retries (seconds)
- `delete_before_sync`: Delete remote folder before deployment

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x deploy.sh
   ```

2. **Python Package Missing**
   ```bash
   pip3 install --user paramiko scp pyyaml tqdm PySocks
   ```

3. **SSH Connection Failed**
   - Check hostname, port, and credentials
   - Verify SSH key permissions: `chmod 600 ~/.ssh/id_rsa`
   - Test SSH manually: `ssh user@hostname -p port`

4. **Proxy Connection Failed**
   - Verify proxy hostname, port, and credentials
   - Try different proxy type (`http` vs `socks5`)
   - Test without proxy first

### Log Files

Check deployment logs for detailed error information:
```bash
tail -f deploy_dev.log
```

### Debug Mode

Run with verbose logging for detailed output:
```bash
./deploy.sh --verbose
```

## Security Notes

- Use SSH key-based authentication when possible
- Store SSH keys with proper permissions (600)
- Avoid storing passwords in config files in production
- Use environment variables for sensitive data
- Regularly rotate SSH keys and passwords

## Examples

### Basic Deployment
```bash
./deploy.sh
```

### Deployment with Custom Paths
```bash
./deploy.sh /home/user/build /var/www/site
```

### Production Deployment
```bash
./deploy.sh --config config.yml --no-delete
```

### Debug Failed Deployment
```bash
./deploy.sh --verbose --config dev.config.yml
```