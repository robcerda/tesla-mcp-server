# Tesla MCP Server

A Model-Controller-Provider server for Tesla vehicles and solar systems. This server allows Claude and other AI assistants to interact with Tesla vehicles and solar systems through a standardized interface.

## Features

- Vehicle status and control
- Solar system monitoring
- Energy usage tracking
- Standardized MCP interface for AI assistants

## Requirements

- Python 3.8 or higher
- Tesla account with API access
- Tesla API credentials (Client ID and Client Secret)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tesla-mcp-server.git
cd tesla-mcp-server
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install `uv` (optional but recommended for faster installation):

On macOS with Homebrew:
```bash
brew install uv
```

Or using the official installer:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

4. Install the package using `uv` (recommended):
```bash
uv pip install -e .
```

Or using `pip`:
```bash
pip install -e .
```

5. Create a `.env` file in the project root with your Tesla API credentials:
```env
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
``` 