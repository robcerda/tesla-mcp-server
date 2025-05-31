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
import asyncio
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tesla_mcp_server.auth import TeslaAuth
from tesla_mcp_server.mcp import TeslaMCP
from tesla_mcp_server.config import PROJECT_ROOT
from mcp.server.fastmcp import FastMCP

# Configure logging to stderr
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("tesla_mcp_server")

# Load environment variables
load_dotenv()

# Initialize Tesla auth and MCP client
tesla_auth = TeslaAuth()
tesla_mcp = TeslaMCP(auth_manager=tesla_auth)

# Initialize FastMCP server
mcp = FastMCP("tesla-mcp")

@mcp.tool()
async def get_vehicles() -> Dict:
    """Get list of all vehicles."""
    try:
        vehicles = await tesla_mcp.get_vehicles()
        return vehicles
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        raise

@mcp.tool()
async def get_vehicle(vehicle_id: str) -> Dict:
    """Get detailed information about a specific vehicle."""
    try:
        vehicle_data = await tesla_mcp.get_vehicle(vehicle_id)
        return vehicle_data
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {str(e)}")
        raise

@mcp.tool()
async def send_command(vehicle_id: str, command: str, parameters: Optional[Dict] = None) -> Dict:
    """Send a command to a vehicle."""
    try:
        result = await tesla_mcp.send_vehicle_command(vehicle_id, command, parameters or {})
        return result
    except Exception as e:
        logger.error(f"Error sending command to vehicle {vehicle_id}: {str(e)}")
        raise

@mcp.tool()
async def get_solar_system(site_id: str) -> Dict:
    """Get status of a solar system."""
    try:
        solar_data = await tesla_mcp.get_solar_system(site_id)
        return solar_data
    except Exception as e:
        logger.error(f"Error getting solar system {site_id}: {str(e)}")
        raise

@mcp.tool()
async def get_solar_history(site_id: str, period: str = "day") -> Dict:
    """Get history of a solar system."""
    try:
        history_data = await tesla_mcp.get_solar_history(site_id, period)
        return history_data
    except Exception as e:
        logger.error(f"Error getting solar history for {site_id}: {str(e)}")
        raise

@mcp.tool()
async def get_system_summary() -> Dict:
    """Get a summary of all Tesla systems."""
    try:
        summary = await tesla_mcp.get_system_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting system summary: {str(e)}")
        raise

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Tesla MCP Server...")
    try:
        # Credentials check before starting the server
        async def startup_check():
            try:
                await tesla_auth.get_valid_token()
                logger.info("Authentication successful. Starting server...")
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                print(f"Authentication failed: {str(e)}", file=sys.stderr)
                sys.exit(1)
        asyncio.run(startup_check())
        mcp.run()
    except Exception as e:
        print(f"Failed to run server: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()
