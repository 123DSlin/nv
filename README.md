# Network Verifier

A system for analyzing and verifying network control plane properties using Batfish.

## Architecture

The system is built with a modular architecture consisting of four main layers:

1. **Data Layer**: Handles network configuration collection and preprocessing
   - Configuration loading and validation
   - Data format conversion
   - Input sanitization

2. **Model Layer**: Focuses on network element modeling
   - Network topology abstraction
   - Device configuration modeling
   - Protocol state representation

3. **Verification Layer**: Executes property verification tasks
   - Property specification
   - Verification execution
   - Result analysis

4. **Presentation Layer**: Handles result visualization and reporting
   - Report generation
   - Network visualization
   - Result export

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd netveri
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Batfish (Choose one of the following methods)

#### Option A: Using Docker (Recommended)
1. Install Docker from [Docker's official website](https://www.docker.com/products/docker-desktop)
2. Pull the Batfish Docker image:
```bash
docker pull batfish/allinone
```
3. Run Batfish container:
```bash
docker run -d --name batfish -p 9995-9997:9995-9997 batfish/allinone
```

#### Option B: Local Installation
1. Install Java 11 or higher
2. Download Batfish from [GitHub releases](https://github.com/batfish/batfish/releases)
3. Extract the downloaded file
4. Add Batfish to your PATH

## Configuration

Create a `.env` file in the project root with the following settings:

```env
BATFISH_HOST=localhost
BATFISH_PORT=9997
CONFIG_DIR=configs
SNAPSHOT_DIR=snapshots
REPORT_DIR=reports
```

## Running the System

### 1. Start Batfish (if not already running)

#### Using Docker:
```bash
# Check if Batfish container is running
docker ps | grep batfish

# If not running, start it
docker start batfish
```

#### Local Installation:
```bash
# Navigate to Batfish directory
cd <batfish-directory>

# Start Batfish service
./batfish
```

### 2. Start the Network Verifier

#### Development Mode (with auto-reload):
```bash
uvicorn src.network_verifier.main:app --reload --host 0.0.0.0 --port 8003
```

#### Production Mode:
```bash
uvicorn src.network_verifier.main:app --host 0.0.0.0 --port 8003
```

### 3. Access the Web Interface
Open your browser and navigate to:
```
http://localhost:8003
```

## Usage

1. Place network configuration files in the `configs` directory
2. Upload configurations through the web interface
3. Run verification tasks:
   - Reachability verification
   - Isolation verification
   - Path location
   - Disjoint path verification
   - Forwarding loop detection
4. View results in the `reports` directory

## Directory Structure

```
netveri/
├── configs/           # Network configuration files
├── reports/          # Verification reports
├── snapshots/        # Configuration snapshots
├── src/              # Source code
│   └── network_verifier/
│       ├── data_layer/        # Data handling
│       ├── model_layer/       # Network modeling
│       ├── verification_layer/ # Property verification
│       └── presentation_layer/ # Result presentation
├── static/           # Static files
├── templates/        # HTML templates
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Troubleshooting

### Common Issues

1. **Batfish Connection Error**
   - Check if Batfish service is running
   - Verify port numbers in .env file
   - Check firewall settings

2. **Configuration Loading Error**
   - Verify file format (supported: .cfg, .txt)
   - Check file permissions
   - Ensure valid network configuration syntax

3. **Verification Engine Error**
   - Check Batfish logs
   - Verify network configuration validity
   - Check system resources

### Logs

- Application logs: `logs/app.log`
- Batfish logs: 
  - Docker: `docker logs batfish`
  - Local: `<batfish-directory>/logs/`

## Development

To run tests:
```bash
pytest tests/
```

## License

MIT License 

## 重启后端命令：pkill -f uvicorn
   ## uvicorn src.network_verifier.main:app --reload --host 0.0.0.0 --port 8003