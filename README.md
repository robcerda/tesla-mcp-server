# Tesla MCP Server

A Model-Controller-Provider server for Tesla vehicles and solar systems. This server allows Claude and other AI assistants to interact with Tesla vehicles and solar systems through a standardized interface.

## ⚠️ Python Version Compatibility

**This project does not support Python 3.13 yet. Please use Python 3.12.**

- If you use [uv](https://github.com/astral-sh/uv), it will automatically create a virtual environment with the correct Python version (if available via pyenv or on your system).
- If you do not have Python 3.12 installed, install it with [pyenv](https://github.com/pyenv/pyenv):
  ```sh
  pyenv install 3.12.3
  ```

## Features

- Vehicle status and control
- Solar system monitoring
- Energy usage tracking
- Standardized MCP interface for AI assistants

## Requirements

- [uv](https://github.com/astral-sh/uv) (recommended for all dependency and environment management)
- Python 3.12 (see above)
- Tesla account with API access
- Tesla API credentials (Client ID and Client Secret). This server authenticates with the Tesla API using the OAuth 2.0 client credentials grant type. For more details on this flow, refer to the official Tesla Fleet API documentation (e.g., at `https://developer.tesla.com/docs/fleet-api`).

## Installation

1. Clone the repository:
```bash
git clone https://github.com/robcerda/tesla-mcp-server.git
cd tesla-mcp-server
```

2. Create and activate a virtual environment using uv (recommended):
```bash
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package in development mode using uv:
```bash
uv pip install -e .
```

If you do not have uv installed:
- On macOS with Homebrew:
  ```bash
  brew install uv
  ```
- Or using the official installer:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

4. Create a `.env` file in the project root (if it doesn't exist already). This file will primarily store your local `ENCRYPTION_KEY` and can also be used for optional configuration overrides like `TESLA_API_BASE_URL`.
Example of `.env` content:
```env
# The ENCRYPTION_KEY is used to encrypt your Tesla API credentials.
# If this key is missing when you run 'python scripts/encrypt_creds.py',
# the script will automatically generate a secure key and save it here.
ENCRYPTION_KEY=your_key_here_will_be_auto_generated_if_missing

# Optional: Override the default Tesla API base URL
# TESLA_API_BASE_URL=https://fleet-api.prd.na.vn.cloud.tesla.com
```
Your `TESLA_CLIENT_ID` and `TESLA_CLIENT_SECRET` are not stored directly in the `.env` file. They are encrypted and stored in a `credentials.enc` file as described below.

## Setting Up Tesla API Credentials (Encrypted)

To set up your Tesla API credentials for the server, run the following script:
```bash
python scripts/encrypt_creds.py
```
This script will guide you through the following:
1.  It will prompt you for your Tesla Client ID and Client Secret.
2.  It will check for an `ENCRYPTION_KEY` in your `.env` file (located in the project root).
3.  If an `ENCRYPTION_KEY` is not found, or the `.env` file doesn't exist (the script will create it if it's missing and you confirm), the script will automatically generate a new secure key and save it to the `.env` file for you. You'll be notified if this happens.
4.  Finally, it will encrypt your Client ID and Secret using this key and save them into a `credentials.enc` file in the project root.

The `credentials.enc` file (containing your encrypted Tesla API credentials) and your `.env` file (containing the `ENCRYPTION_KEY`) should not be committed to version control if your repository is public or shared. The provided `.gitignore` file is already configured to ignore these files.

## Running the MCP Server

After installation and setting up your credentials, you can run the MCP server using:

```bash
mcp install src/tesla_mcp_server/server.py --name "Tesla MCP" --with-editable . --env-file .env
```

This command:
- Installs the server as an MCP tool named "Tesla MCP"
- Uses the editable install mode for development
- Loads environment variables from your `.env` file

The server provides the following tools:
- `get_system_status`: Get the current status of all Tesla systems
- `get_solar_status`: Get the current status of the solar system
- `get_solar_history`: Get historical data for the solar system
- `get_vehicle_status`: Get the status of all vehicles or a specific vehicle

You can use these tools through Claude or any other MCP-compatible AI assistant.