# Deploy Tool

## Phase 1

### Specs

Viết 1 script python cho phép sync source từ local lên remote server (ssh bằng proxy)

**Input:**

- đường dẫn thư mục ở local
- đường dẫn thư mục ở remote

**Config:**
thông tin ssh sẽ config ở file yml

**Feature More:**

- Hiển thị tiến độ sync source (progress bar / logging).
- Cho phép nén source ở local và giải nén ở remote để tăng tốc độ truyền tải.
- Xử lý retry khi kết nối gián đoạn.
- Kiểm tra checksum để đảm bảo file không bị lỗi sau khi sync.
- Phía remote có thể là ubuntu, amazon linux, centos nên đảm bảo package 2 bên phải tương thích
- Có thể run trên mọi nền tảng window, ubuntu, linux

### Tech Stack

Python 3.x
Thư viện gợi ý: paramiko, scp/rsync, tqdm, pyyaml, tarfile/zipfile.

### CheckList Todo

- [x] Set up project structure and configuration
- [x] Create SSH configuration parser using PyYAML
- [x] Implement basic SSH connection with paramiko
- [x] Add file compression/decompression functionality
- [x] Implement file transfer with progress tracking
- [x] Add checksum verification for integrity
- [x] Implement retry mechanism for connection failures
- [x] Add cross-platform compatibility checks
- [x] Create main CLI interface
- [x] Add logging and error handling

### Phase 1 Implementation Complete

The deploy tool has been fully implemented with all requested features:

### Files Created:
- `deploy_tool.py` - Main deployment script
- `config.yml` - Configuration template
- `requirements.txt` - Python dependencies
- `setup.py` - Cross-platform setup script
- `README.md` - Documentation

### Key Features Implemented:
- SSH connection with proxy support
- File compression (tar.gz/zip) for faster transfers
- Progress tracking with tqdm
- SHA256 checksum verification
- Automatic retry mechanism
- Cross-platform compatibility (Windows/Linux/macOS)
- Comprehensive logging and error handling
- CLI interface with argument parsing

### Usage:
```bash
python setup.py              # Initial setup
python deploy_tool.py /local/path /remote/path
```

