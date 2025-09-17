# Deploy Tool

A Python-based deployment tool for syncing source code from local to remote servers via SSH with proxy support.

## Features

- ✅ SSH connection with key-based or password authentication
- ✅ Proxy support for SSH connections
- ✅ File compression (tar.gz, zip) for faster transfers
- ✅ Progress tracking with progress bars
- ✅ Checksum verification for file integrity
- ✅ Automatic retry on connection failures
- ✅ Cross-platform support (Windows, Linux, macOS)
- ✅ Comprehensive logging
- ✅ YAML-based configuration

## Installation

1. Clone or download this repository
2. Run the setup script:
   ```bash
   python setup.py
   ```

## Configuration

The tool uses two configuration files with automatic detection:

### File Priority:
1. `dev.config.yml` - Development settings (auto-detected, ignored by git)
2. `config.yml` - Production settings (committed to git)

### Development Configuration (`dev.config.yml`):
```yaml
paths:
  local: "/path/to/local/dev/source"
  remote: "/path/to/remote/dev/destination"
ssh:
  hostname: "dev-server.com"
  username: "dev-user"
  key_file: "~/.ssh/id_rsa_dev"
deploy:
  compression: true
  retry_attempts: 3
  delete_before_sync: true  # Safer in dev environment
logging:
  level: "DEBUG"
  file: "deploy_dev.log"
```

### Production Configuration (`config.yml`):
```yaml
paths:
  local: "/path/to/local/source"
  remote: "/path/to/remote/destination"
ssh:
  hostname: "prod-server.com"
  username: "prod-user"
  key_file: "~/.ssh/id_rsa_prod"
deploy:
  compression: true
  retry_attempts: 5
  delete_before_sync: false  # DANGEROUS in production
logging:
  level: "INFO"
  file: "deploy_prod.log"
```

### Configuration Priority Logic:
- If `dev.config.yml` exists → Use it (development mode)
- Else use `config.yml` (production mode)
- Override with `-c` flag for specific file

## Usage

### Method 1: Use paths from config file (recommended)
Set paths in your config file and run without arguments:
```bash
python deploy_tool.py
```

### Method 2: Override paths via command line
```bash
python deploy_tool.py /local/path /remote/path
```

### Method 3: Mix config and CLI (CLI overrides config)
```bash
python deploy_tool.py /custom/local/path    # Uses remote path from config
```

### Additional Options

Force specific config file:
```bash
python deploy_tool.py -c config.yml
python deploy_tool.py -c dev.config.yml /local/path /remote/path
```

Verbose output:
```bash
python deploy_tool.py -v
```

### Delete Remote Folder Options

Force delete remote folder (overrides config):
```bash
python deploy_tool.py --delete
```

Force disable delete (overrides config):
```bash
python deploy_tool.py --no-delete
```

Combine with other options:
```bash
python deploy_tool.py --delete -v /local/path /remote/path
```

### Priority Logic:
- **Paths:** CLI arguments → Config file → Error
- **Delete:** CLI flags (--delete/--no-delete) → Config file → Default (false)

### ⚠️ Safety Notes:
- `delete_before_sync: true` will **permanently delete** the remote folder
- Use with caution in production environments
- Recommended: `true` for dev, `false` for production

## Requirements

- Python 3.7+
- SSH client (for proxy connections)
- Required Python packages (installed via setup.py):
  - paramiko>=2.12.0
  - scp>=0.14.5
  - tqdm>=4.65.0
  - PyYAML>=6.0

## Compatibility

Tested on:
- Windows 10/11
- Ubuntu 18.04+
- Amazon Linux 2
- CentOS 7+
- macOS 10.15+

## License

MIT License