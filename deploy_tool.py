#!/usr/bin/env python3
"""
Deploy Tool - Sync source from local to remote server via SSH
Author: Assistant
Version: 1.0.0
"""

import os
import sys
import argparse
import logging
import hashlib
import tarfile
import zipfile
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any

import yaml
import paramiko
from paramiko import AutoAddPolicy
from scp import SCPClient
from tqdm import tqdm


class DeployTool:
    """Main deploy tool class for syncing files to remote servers."""

    def __init__(self, config_file: str = None):
        """Initialize deploy tool with configuration."""
        config_file = self._determine_config_file(config_file)
        self.config = self._load_config(config_file)
        self.ssh_client = None
        self.scp_client = None
        self.proxy_client = None
        self._setup_logging()

    def _determine_config_file(self, config_file: str = None) -> str:
        """Determine which config file to use with priority logic."""
        if config_file:
            # If explicitly specified, use it
            return config_file

        # Check for dev.config.yml first (development priority)
        if os.path.exists("dev.config.yml"):
            print("Using development configuration: dev.config.yml")
            return "dev.config.yml"

        # Fallback to config.yml (production)
        if os.path.exists("config.yml"):
            print("Using production configuration: config.yml")
            return "config.yml"

        # If neither exists, create template and exit
        print("ERROR: No configuration file found. Please create config.yml or dev.config.yml")
        sys.exit(1)

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            return config
        except FileNotFoundError:
            print(f"ERROR: Configuration file {config_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"ERROR: Error parsing configuration file: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config['logging']['level'])
        log_format = '%(asctime)s - %(levelname)s - %(message)s'

        # Get root logger and clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Set log level
        root_logger.setLevel(log_level)

        # Create formatter
        formatter = logging.Formatter(log_format)

        # Create file handler
        file_handler = logging.FileHandler(self.config['logging']['file'])
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Also configure paramiko logging to be less verbose unless in DEBUG mode
        paramiko_logger = logging.getLogger('paramiko')
        if log_level > logging.DEBUG:
            paramiko_logger.setLevel(logging.WARNING)

        # Log that logging is now configured
        logging.info(f"Logging configured - Level: {self.config['logging']['level']}, File: {self.config['logging']['file']}")

    def connect_ssh(self) -> bool:
        """Establish SSH connection to remote server."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(AutoAddPolicy())

            ssh_config = self.config['ssh']

            # Setup connection parameters
            connect_kwargs = {
                'hostname': ssh_config['hostname'],
                'port': ssh_config['port'],
                'username': ssh_config['username'],
                'timeout': 30
            }

            # Use key-based authentication if available
            if ssh_config.get('key_file'):
                key_file = os.path.expanduser(ssh_config['key_file'])
                if os.path.exists(key_file):
                    connect_kwargs['key_filename'] = key_file
                    logging.info(f"Using key file: {key_file}")

            # Fallback to password authentication
            if ssh_config.get('password'):
                connect_kwargs['password'] = ssh_config['password']
                logging.info("Using password authentication")

            # Handle proxy connection if configured
            if ssh_config.get('proxy', {}).get('hostname'):
                proxy_config = ssh_config['proxy']
                proxy_type = proxy_config.get('type', 'auto').lower()
                logging.info(f"Setting up {proxy_type} proxy connection through: {proxy_config['hostname']}")

                try:
                    import socket

                    if proxy_type == 'socks5' or proxy_type == 'auto':
                        # Try SOCKS5 proxy
                        try:
                            import socks
                            logging.info("Attempting SOCKS5 proxy connection...")

                            # Create a socket through SOCKS proxy
                            socks.set_default_proxy(socks.SOCKS5, proxy_config['hostname'], proxy_config['port'])
                            sock = socks.socksocket()
                            sock.settimeout(30)

                            sock.connect((ssh_config['hostname'], ssh_config['port']))
                            connect_kwargs['sock'] = sock
                            logging.info(f"SOCKS5 proxy connection established to {ssh_config['hostname']}")

                        except ImportError:
                            if proxy_type == 'socks5':
                                logging.error("PySocks not installed. Install with: pip install PySocks")
                                raise
                            else:
                                logging.info("PySocks not available, trying HTTP CONNECT...")
                                raise Exception("SOCKS5 not available")

                        except Exception as socks_error:
                            if proxy_type == 'socks5':
                                raise socks_error
                            logging.warning(f"SOCKS5 proxy failed: {socks_error}")
                            raise Exception("SOCKS5 failed, trying HTTP")

                    if proxy_type == 'http' or proxy_type == 'auto':
                        # HTTP CONNECT proxy
                        logging.info("Attempting HTTP CONNECT proxy...")

                        # Create HTTP CONNECT tunnel
                        proxy_host = proxy_config['hostname']
                        proxy_port = proxy_config['port']
                        target_host = ssh_config['hostname']
                        target_port = ssh_config['port']

                        # Create socket to proxy
                        proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        proxy_sock.settimeout(30)
                        proxy_sock.connect((proxy_host, proxy_port))

                        # Send CONNECT request
                        connect_request = f"CONNECT {target_host}:{target_port} HTTP/1.1\r\n"

                        if proxy_config.get('username') and proxy_config.get('password'):
                            import base64
                            auth_string = f"{proxy_config['username']}:{proxy_config['password']}"
                            auth_bytes = base64.b64encode(auth_string.encode()).decode()
                            connect_request += f"Proxy-Authorization: Basic {auth_bytes}\r\n"

                        connect_request += "\r\n"

                        proxy_sock.send(connect_request.encode())
                        response = proxy_sock.recv(4096).decode()

                        # Check for successful HTTP response (200 OK or Connection established)
                        if "200" in response and ("OK" in response or "Connection established" in response):
                            connect_kwargs['sock'] = proxy_sock
                            logging.info(f"HTTP CONNECT proxy established to {ssh_config['hostname']}")
                        else:
                            proxy_sock.close()
                            raise Exception(f"HTTP CONNECT failed: {response}")

                except Exception as proxy_error:
                    if proxy_type != 'auto':
                        logging.error(f"Failed to establish {proxy_type} proxy connection: {proxy_error}")
                        raise proxy_error
                    else:
                        logging.error(f"Failed to establish proxy connection: {proxy_error}")
                        logging.info("Attempting direct connection without proxy...")
                        # Continue with direct connection

            # Attempt connection with retry
            max_retries = self.config['deploy']['retry_attempts']
            retry_delay = self.config['deploy']['retry_delay']

            for attempt in range(max_retries):
                try:
                    self.ssh_client.connect(**connect_kwargs)
                    logging.info(f"SSH connection established to {ssh_config['hostname']}")

                    # Initialize SCP client
                    self.scp_client = SCPClient(self.ssh_client.get_transport())
                    return True

                except Exception as e:
                    logging.warning(f"SSH connection attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        logging.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logging.error("All SSH connection attempts failed")
                        return False

        except Exception as e:
            logging.error(f"Error establishing SSH connection: {e}")
            return False

    def disconnect_ssh(self):
        """Close SSH, SCP, and proxy connections."""
        if self.scp_client:
            self.scp_client.close()
            self.scp_client = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None
        if self.proxy_client:
            self.proxy_client.close()
            self.proxy_client = None
        logging.info("SSH and proxy connections closed")

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def compress_directory(self, source_path: str, temp_dir: str) -> str:
        """Compress directory to temporary archive."""
        source_name = os.path.basename(source_path.rstrip('/\\'))
        compression_format = self.config['deploy']['compression_format']

        if compression_format == 'tar.gz':
            archive_name = f"{source_name}.tar.gz"
            archive_path = os.path.join(temp_dir, archive_name)

            with tarfile.open(archive_path, "w:gz") as tar:
                # Add contents of the directory, not the directory itself
                for item in os.listdir(source_path):
                    item_path = os.path.join(source_path, item)
                    tar.add(item_path, arcname=item)

        elif compression_format == 'zip':
            archive_name = f"{source_name}.zip"
            archive_path = os.path.join(temp_dir, archive_name)

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Make arcname relative to source_path, not its parent
                        arcname = os.path.relpath(file_path, source_path)
                        zipf.write(file_path, arcname)
        else:
            raise ValueError(f"Unsupported compression format: {compression_format}")

        logging.info(f"Created archive: {archive_path}")
        return archive_path

    def decompress_remote(self, archive_path: str, remote_path: str) -> bool:
        """Decompress archive on remote server."""
        try:
            compression_format = self.config['deploy']['compression_format']

            if compression_format == 'tar.gz':
                cmd = f"cd {remote_path} && tar -xzf {os.path.basename(archive_path)}"
            elif compression_format == 'zip':
                cmd = f"cd {remote_path} && unzip -o {os.path.basename(archive_path)}"
            else:
                raise ValueError(f"Unsupported compression format: {compression_format}")

            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                logging.info("Archive decompressed successfully on remote server")
                # Clean up archive file
                cleanup_cmd = f"rm {remote_path}/{os.path.basename(archive_path)}"
                self.ssh_client.exec_command(cleanup_cmd)
                return True
            else:
                error_output = stderr.read().decode()
                logging.error(f"Decompression failed: {error_output}")
                return False

        except Exception as e:
            logging.error(f"Error during remote decompression: {e}")
            return False

    def verify_remote_checksum(self, local_file: str, remote_file: str) -> bool:
        """Verify file integrity using checksum comparison."""
        try:
            local_checksum = self.calculate_checksum(local_file)

            # Calculate remote checksum
            cmd = f"sha256sum {remote_file}"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                remote_output = stdout.read().decode().strip()
                remote_checksum = remote_output.split()[0]

                if local_checksum == remote_checksum:
                    logging.info("Checksum verification passed")
                    return True
                else:
                    logging.error(f"Checksum mismatch: local={local_checksum}, remote={remote_checksum}")
                    return False
            else:
                error_output = stderr.read().decode()
                logging.warning(f"Could not verify remote checksum: {error_output}")
                return True  # Continue deployment if checksum verification fails

        except Exception as e:
            logging.warning(f"Checksum verification failed: {e}")
            return True  # Continue deployment if checksum verification fails

    def delete_remote_folder(self, remote_path: str) -> bool:
        """Delete remote folder if it exists."""
        try:
            # Check if remote folder exists
            cmd = f"test -d {remote_path}"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()

            if exit_status == 0:
                # Folder exists, delete it
                logging.warning(f"Deleting remote folder: {remote_path}")
                delete_cmd = f"rm -rf {remote_path}"
                stdin, stdout, stderr = self.ssh_client.exec_command(delete_cmd)
                exit_status = stdout.channel.recv_exit_status()

                if exit_status == 0:
                    logging.info(f"Remote folder deleted successfully: {remote_path}")
                    return True
                else:
                    error_output = stderr.read().decode()
                    logging.error(f"Failed to delete remote folder: {error_output}")
                    return False
            else:
                logging.info(f"Remote folder does not exist: {remote_path}")
                return True

        except Exception as e:
            logging.error(f"Error deleting remote folder: {e}")
            return False

    def deploy(self, local_path: str = None, remote_path: str = None, force_delete: bool = None) -> bool:
        """Deploy local directory to remote server."""
        try:
            # Use config paths if not provided via CLI
            if not local_path:
                local_path = self.config.get('paths', {}).get('local')
                if not local_path:
                    logging.error("Local path not provided via CLI or config")
                    return False

            if not remote_path:
                remote_path = self.config.get('paths', {}).get('remote')
                if not remote_path:
                    logging.error("Remote path not provided via CLI or config")
                    return False

            # Expand user path for local
            local_path = os.path.expanduser(local_path)

            logging.info(f"Starting deployment: {local_path} -> {remote_path}")

            # Validate local path
            if not os.path.exists(local_path):
                logging.error(f"Local path does not exist: {local_path}")
                return False

            # Connect to remote server
            if not self.connect_ssh():
                return False

            # Determine if we should delete remote folder before sync
            should_delete = force_delete
            if should_delete is None:
                should_delete = self.config.get('deploy', {}).get('delete_before_sync', False)

            # Delete remote folder if requested
            if should_delete:
                if not self.delete_remote_folder(remote_path):
                    logging.error("Failed to delete remote folder, aborting deployment")
                    return False

            # Create remote directory if it doesn't exist
            cmd = f"mkdir -p {remote_path}"
            self.ssh_client.exec_command(cmd)

            success = False
            temp_dir = None

            try:
                if self.config['deploy']['compression']:
                    # Compression mode
                    with tempfile.TemporaryDirectory() as temp_dir:
                        logging.info("Compressing source directory...")
                        archive_path = self.compress_directory(local_path, temp_dir)

                        # Transfer compressed file with progress
                        logging.info("Transferring compressed archive...")
                        remote_archive = f"{remote_path}/{os.path.basename(archive_path)}"

                        file_size = os.path.getsize(archive_path)

                        # Manual progress tracking for real-time updates
                        logging.info(f"Uploading {file_size:,} bytes...")

                        # Use a custom approach for real-time progress
                        import threading
                        import time

                        progress_data = {'uploaded': 0, 'total': file_size, 'finished': False}

                        def progress_monitor():
                            """Monitor and display upload progress"""
                            while not progress_data['finished']:
                                if progress_data['uploaded'] > 0:
                                    percent = (progress_data['uploaded'] / progress_data['total']) * 100
                                    mb_uploaded = progress_data['uploaded'] / (1024 * 1024)
                                    mb_total = progress_data['total'] / (1024 * 1024)
                                    print(f"\rUpload progress: {percent:.1f}% ({mb_uploaded:.2f}/{mb_total:.2f} MB)", end='', flush=True)
                                time.sleep(0.5)

                        # Start progress monitor in background
                        monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
                        monitor_thread.start()

                        try:
                            # Try with progress callback first
                            def progress_callback(filename, size, sent):
                                progress_data['uploaded'] = sent

                            self.scp_client.put(archive_path, remote_archive, progress=progress_callback)

                        except (TypeError, AttributeError):
                            # Fallback: Manual chunked upload with progress
                            logging.info("Using manual upload with progress tracking...")

                            with open(archive_path, 'rb') as local_file:
                                # Use SFTP for chunked upload with progress
                                sftp = self.ssh_client.open_sftp()
                                with sftp.open(remote_archive, 'wb') as remote_file:
                                    chunk_size = self.config['deploy']['chunk_size']
                                    while True:
                                        chunk = local_file.read(chunk_size)
                                        if not chunk:
                                            break
                                        remote_file.write(chunk)
                                        progress_data['uploaded'] += len(chunk)
                                sftp.close()

                        progress_data['finished'] = True
                        print()  # New line after progress
                        logging.info("Upload completed!")

                        # Verify checksum if enabled
                        if self.config['deploy']['checksum_verify']:
                            if not self.verify_remote_checksum(archive_path, remote_archive):
                                logging.error("Checksum verification failed")
                                return False

                        # Decompress on remote server
                        if self.decompress_remote(archive_path, remote_path):
                            success = True

                else:
                    # Direct transfer mode
                    logging.info("Transferring files directly...")

                    # Use rsync-like functionality via SCP
                    if os.path.isdir(local_path):
                        self.scp_client.put(local_path, remote_path, recursive=True)
                    else:
                        self.scp_client.put(local_path, remote_path)

                    success = True

                if success:
                    logging.info("Deployment completed successfully!")
                else:
                    logging.error("Deployment failed!")

                return success

            except Exception as e:
                logging.error(f"Deployment error: {e}")
                return False

            finally:
                self.disconnect_ssh()

        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            return False


def main():
    """Main entry point for the deploy tool."""
    parser = argparse.ArgumentParser(description="Deploy Tool - Sync source to remote server")
    parser.add_argument("local_path", nargs='?', help="Local directory path to deploy (optional if set in config)")
    parser.add_argument("remote_path", nargs='?', help="Remote directory path destination (optional if set in config)")
    parser.add_argument("-c", "--config", help="Configuration file path (default: auto-detect)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    # Delete options (mutually exclusive)
    delete_group = parser.add_mutually_exclusive_group()
    delete_group.add_argument("--delete", action="store_true",
                             help="Force delete remote folder before sync (overrides config)")
    delete_group.add_argument("--no-delete", action="store_true",
                             help="Force disable delete remote folder (overrides config)")

    args = parser.parse_args()

    # Override logging level if verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Determine delete override
    force_delete = None
    if args.delete:
        force_delete = True
    elif args.no_delete:
        force_delete = False

    # Initialize deploy tool
    deploy_tool = DeployTool(args.config)

    # Perform deployment
    success = deploy_tool.deploy(args.local_path, args.remote_path, force_delete)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()