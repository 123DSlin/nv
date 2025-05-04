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

## Installation

1. Install Python 3.8 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Batfish (follow instructions at https://github.com/batfish/batfish)

## Configuration

Create a `.env` file in the project root with the following settings:

```env
BATFISH_HOST=localhost
BATFISH_PORT=9997
CONFIG_DIR=configs
SNAPSHOT_DIR=snapshots
REPORT_DIR=reports
```

## Usage

1. Place network configuration files in the `configs` directory
2. Run the verification process:
   ```bash
   python -m network_verifier.main
   ```
3. View results in the `reports` directory

## Development

To run tests:
```bash
pytest tests/
```

## License

MIT License 