"""
Tesla MCP Server

This module implements a Model Context Protocol (MCP) server for connecting
Claude with the Tesla API. It provides tools for retrieving and managing
Tesla vehicle and solar system data.

Main Features:
    - Vehicle status and control
    - Solar system monitoring
    - Energy usage tracking
    - Error handling with user-friendly messages
    - Configurable parameters with environment variable support

Usage:
    This server is designed to be run as a standalone script and exposes several MCP tools
    for use with Claude Desktop or other MCP-compatible clients. The server loads configuration
    from environment variables (optionally via a .env file) and communicates with the Tesla API.

    To run the server:
        $ python src/tesla_mcp_server/server.py

    MCP tools provided:
        - get_system_status
        - get_solar_status
        - get_solar_history
        - get_vehicle_status

    See the README for more details on configuration and usage.
"""

import os
import sys
import logging
import importlib
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tesla_mcp_server.auth import TeslaAuth
from tesla_mcp_server.mcp import TeslaMCP
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("tesla_mcp_server")

# Debug MCP package structure
print("Debugging MCP package structure:", file=sys.stderr)
try:
    import mcp
    print(f"MCP package location: {mcp.__file__}", file=sys.stderr)
    print(f"MCP package contents: {dir(mcp)}", file=sys.stderr)
    
    # Try to import FastMCP
    try:
        from mcp.server.fastmcp import FastMCP
        print("Successfully imported FastMCP", file=sys.stderr)
    except ImportError as e:
        print(f"Failed to import FastMCP: {str(e)}", file=sys.stderr)
        # Try to find the correct module
        print("Searching for FastMCP in mcp package...", file=sys.stderr)
        for name in dir(mcp):
            if 'fast' in name.lower() or 'server' in name.lower():
                print(f"Found potential module: {name}", file=sys.stderr)
except ImportError as e:
    print(f"Failed to import mcp package: {str(e)}", file=sys.stderr)

# Load environment variables
load_dotenv()

# Initialize Tesla auth and MCP client
tesla_auth = TeslaAuth()
tesla_mcp = TeslaMCP(auth_manager=tesla_auth)

# Initialize FastMCP server
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("tesla-mcp")
    print("Successfully initialized FastMCP server", file=sys.stderr)
except Exception as e:
    print(f"Failed to initialize FastMCP server: {str(e)}", file=sys.stderr)
    raise

@mcp.tool()
async def get_system_status() -> str:
    """Get the current status of all Tesla systems."""
    try:
        logger.info("Getting system status...")
        summary = await tesla_mcp.get_system_summary()
        return format_system_summary(summary)
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
async def get_solar_status() -> str:
    """Get the current status of the solar system."""
    try:
        logger.info("Getting solar status...")
        systems = await tesla_mcp.get_solar_systems()
        if not systems:
            return "No solar systems found."
        site_id = systems[0]['id']
        status = await tesla_mcp.get_solar_system(site_id)
        return format_solar_status(status)
    except Exception as e:
        logger.error(f"Error getting solar status: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
async def get_solar_history(period: str = "day") -> str:
    """Get historical data for the solar system.
    
    Args:
        period: The time period to get history for (day, week, month, year)
    """
    try:
        logger.info(f"Getting solar history for period: {period}...")
        systems = await tesla_mcp.get_solar_systems()
        if not systems:
            return "No solar systems found."
        site_id = systems[0]['id']
        history = await tesla_mcp.get_solar_history(site_id, period)
        return format_solar_history(history, period)
    except Exception as e:
        logger.error(f"Error getting solar history: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
async def get_vehicle_status(vehicle_name: Optional[str] = None) -> str:
    """Get the status of all vehicles or a specific vehicle.
    
    Args:
        vehicle_name: Optional name of a specific vehicle to get status for
    """
    try:
        logger.info(f"Getting vehicle status for: {vehicle_name or 'all vehicles'}...")
        vehicles = await tesla_mcp.get_vehicles()
        if not vehicles:
            return "No vehicles found."
        
        if vehicle_name:
            for vehicle in vehicles:
                if vehicle['display_name'].lower() == vehicle_name.lower():
                    status = await tesla_mcp.get_vehicle(vehicle['id'])
                    return format_vehicle_status(status)
            return f"No vehicle found with name: {vehicle_name}"
        
        return format_vehicles_summary(vehicles)
    except Exception as e:
        logger.error(f"Error getting vehicle status: {str(e)}")
        return f"Error: {str(e)}"

def format_system_summary(summary: dict) -> str:
    """Format system summary into a readable string."""
    if "error" in summary:
        return f"Error getting system status: {summary['error']}"
    
    response = ["Tesla System Status:"]
    
    if summary.get("vehicles"):
        response.append("\nVehicles:")
        for vehicle in summary["vehicles"]:
            response.append(f"- {vehicle['name']}: {vehicle['state']}")
            if vehicle.get('battery_level') is not None:
                response.append(f"  Battery: {vehicle['battery_level']}%")
    
    if summary.get("solar_systems"):
        response.append("\nSolar Systems:")
        for system in summary["solar_systems"]:
            response.append(f"- {system['name']}: {system['status']}")
            if system.get('total_power') is not None:
                response.append(f"  Current Power: {system['total_power']}W")
            if system.get('battery_level') is not None:
                response.append(f"  Battery: {system['battery_level']}%")
    
    return "\n".join(response)

def format_solar_status(status: dict) -> str:
    """Format solar system status into a readable string."""
    response = [f"Solar System Status for {status.get('site_name', 'Unknown')}:"]
    
    if status.get('total_power') is not None:
        response.append(f"Current Power Generation: {status['total_power']}W")
    if status.get('energy_today') is not None:
        response.append(f"Energy Generated Today: {status['energy_today']}kWh")
    if status.get('battery_level') is not None:
        response.append(f"Battery Level: {status['battery_level']}%")
    if status.get('grid_power') is not None:
        response.append(f"Grid Power: {status['grid_power']}W")
    
    return "\n".join(response)

def format_solar_history(history: dict, period: str) -> str:
    """Format solar history into a readable string."""
    response = [f"Solar System History ({period}):"]
    
    if "response" in history:
        data = history["response"]
        if "time_series" in data:
            for point in data["time_series"]:
                timestamp = point.get("timestamp", "Unknown")
                solar = point.get("solar", 0)
                battery = point.get("battery", 0)
                grid = point.get("grid", 0)
                response.append(f"\n{timestamp}:")
                response.append(f"  Solar: {solar}W")
                response.append(f"  Battery: {battery}W")
                response.append(f"  Grid: {grid}W")
    
    return "\n".join(response)

def format_vehicle_status(status: dict) -> str:
    """Format vehicle status into a readable string."""
    response = [f"Vehicle Status for {status.get('display_name', 'Unknown')}:"]
    
    response.append(f"State: {status.get('state', 'Unknown')}")
    if status.get('battery_level') is not None:
        response.append(f"Battery: {status['battery_level']}%")
    
    return "\n".join(response)

def format_vehicles_summary(vehicles: list) -> str:
    """Format multiple vehicles status into a readable string."""
    response = ["Vehicle Status:"]
    
    for vehicle in vehicles:
        response.append(f"\n{vehicle['display_name']}:")
        response.append(f"State: {vehicle['state']}")
        if vehicle.get('battery_level') is not None:
            response.append(f"Battery: {vehicle['battery_level']}%")
    
    return "\n".join(response)

class TeslaMCPServer:
    """Tesla MCP Server class for MCP CLI compatibility."""
    
    def __init__(self):
        """Initialize the Tesla MCP Server."""
        self.mcp = mcp
    
    def run(self):
        """Run the Tesla MCP Server."""
        self.mcp.run()

# Run the server
if __name__ == "__main__":
    logger.info("Starting Tesla MCP Server...")
    try:
        mcp.run()
    except Exception as e:
        print(f"Failed to run server: {str(e)}", file=sys.stderr)
        raise
