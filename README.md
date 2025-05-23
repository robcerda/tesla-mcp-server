# Tesla MCP Server

A Message Control Protocol (MCP) server for interacting with Tesla's Fleet API. This server provides a standardized interface for accessing Tesla vehicle data, solar system information, and sending commands.

## Features

- Vehicle data and control
- Solar system monitoring
- Energy site management
- Health status monitoring
- Standardized MCP interface for AI assistants

## Requirements

- Python 3.9 or higher
- Tesla Fleet API credentials (Client ID and Client Secret)

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd tesla-mcp-server
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Tesla Fleet API credentials:
```env
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
```

## Running the Server

1. Make sure you're in the project directory and your virtual environment is activated:
```bash
cd tesla-mcp-server
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Start the server:
```bash
uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`

## API Endpoints

### Health Check
- `GET /health` - Check server health status

### Vehicle Endpoints
- `GET /vehicles` - List all vehicles
- `GET /vehicles/{vehicle_id}` - Get specific vehicle details
- `POST /vehicles/{vehicle_id}/commands` - Send commands to a vehicle

### Solar System Endpoints
- `GET /solar` - List all solar systems
- `GET /solar/{site_id}` - Get specific solar system details
- `POST /solar/{site_id}/commands` - Send commands to a solar system
- `GET /solar/{site_id}/history` - Get solar system history
- `GET /solar/{site_id}/telemetry` - Get solar system telemetry data

## Authentication

This server uses Tesla's OAuth 2.0 authentication flow. You'll need to:

1. Register your application with Tesla at https://developer.tesla.com
2. Obtain client credentials (Client ID and Client Secret)
3. Configure the appropriate scopes for your application:
   - `vehicle_device_data`
   - `vehicle_commands`
   - `vehicle_telemetry`
   - `energy_device_data`

For more information, refer to the [Tesla Fleet API Documentation](https://developer.tesla.com/docs/fleet-api).

## Using with AI Assistants

The server implements the Message Control Protocol (MCP) interface, making it compatible with AI assistants like Claude. The server can handle requests for:

- Vehicle status and control
- Solar system monitoring
- Energy site management
- System health checks

Example usage with an AI assistant:
```python
# Example of how an AI assistant might interact with the server
import requests

# Get vehicle status
response = requests.get("http://localhost:8000/vehicles")
vehicles = response.json()

# Get solar system status
response = requests.get("http://localhost:8000/solar")
solar_systems = response.json()

# Send a command to a vehicle
command = {
    "command": "climate_on",
    "parameters": {"temperature": 22}
}
response = requests.post("http://localhost:8000/vehicles/{vehicle_id}/commands", json=command)
```

## Error Handling

The server includes comprehensive error handling and logging. Common error scenarios include:

- Invalid authentication credentials
- Network connectivity issues
- Invalid command parameters
- Rate limiting

Check the server logs for detailed error information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your chosen license] 