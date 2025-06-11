# Tesla MCP Server

Model Context Protocol (MCP) server for connecting Claude with the Tesla Owner API. It provides tools for authentication and data retrieval for Tesla vehicles and solar systems.

## Requirements

* Python 3.11
* Model Context Protocol (MCP) Python SDK
* httpx
* python-dotenv

## Setup

### 1. Install uv (recommended)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone this repository

```bash
git clone https://github.com/yourusername/tesla-mcp-server.git
cd tesla-mcp-server
```

### 3. Create and activate a virtual environment

```bash
# Create virtual environment
uv venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate
```

### 4. Sync project dependencies

```bash
uv sync
```

## Usage

### Authentication Setup

This server uses Tesla's **Owner API** and implements a secure OAuth2 authentication flow. **Before using the server with Claude Desktop, you must first run the authentication setup script.**

#### 1. Run Authentication Setup

**IMPORTANT:** You must run this setup script before using the server with Claude:

```bash
python setup_auth.py
```

This script will:
- Prompt you to authenticate via your browser
- Walk you through the Tesla OAuth2 flow
- Create a `refresh_token.txt` file for future sessions
- Test the API connection to ensure everything works

**Do not commit `refresh_token.txt` to version control.**

#### 2. Authentication Flow Details

- On first run of `setup_auth.py`, you will be prompted to authenticate via your browser
- Follow the instructions in the terminal to complete the OAuth2 flow
- After successful authentication, a `refresh_token.txt` file will be created and used for future sessions
- The refresh token will be automatically used by the MCP server for subsequent API calls

### Configure Claude Desktop

To use this server with Claude Desktop, you need to add it to your Claude Desktop configuration.

1. Run the following from the `tesla_mcp_server` directory to configure Claude Desktop:

```bash
mcp install src/tesla_mcp_server/server.py --name "Tesla" --with-editable .
```

2. If you open your Claude Desktop App configuration file `claude_desktop_config.json`, it should look like this:

```json
{
  "mcpServers": {
    "Tesla": {
      "command": "/Users/<USERNAME>/.cargo/bin/uv",
      "args": [
        "run",
        "--with",
        "mcp[cli]",
        "--with-editable",
        "/path/to/tesla-mcp-server",
        "mcp",
        "run",
        "/path/to/tesla-mcp-server/src/tesla_mcp_server/server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Where `/path/to/` is the path to the `tesla-mcp-server` code folder in your system.

3. Restart Claude Desktop.

### Use the MCP server with Claude

Once the server is running and Claude Desktop is configured, you can use the following tools to interact with your Tesla systems:

* `tesla_auth_status`: Check Tesla authentication status
* `get_vehicles`: Get a list of all your vehicles
* `get_vehicle`: Get detailed information about a specific vehicle
* `send_command`: Send a command to a vehicle
* `get_solar_system`: Get status of a solar system
* `get_solar_history`: Get history of a solar system
* `get_system_summary`: Get a summary of all Tesla systems

#### Re-authentication
- If you ever need to re-authenticate, simply delete `refresh_token.txt` and run `python setup_auth.py` again.

## Development and testing

Install development dependencies and run the test suite with:

```bash
uv sync --all-extras
pytest -v tests
```

### Running the server locally

To start the server manually (useful when developing or testing), run:

```bash
mcp run src/tesla_mcp_server/server.py
```

## License

The GNU General Public License v3.0
