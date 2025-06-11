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
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import mcp.types as types

from tesla_mcp_server.auth import TeslaAuth
from tesla_mcp_server.mcp import TeslaMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_async(coro):
    """Run async function in a new thread with its own event loop."""
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error in async execution: {e}")
            raise
        finally:
            try:
                # Cancel any remaining tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
            except Exception as e:
                logger.error(f"Error closing event loop: {e}")
    
    with ThreadPoolExecutor() as executor:
        future = executor.submit(_run)
        return future.result(timeout=30)

# Initialize Tesla auth manager (preserving existing auth mechanism)
tesla_auth = TeslaAuth()

# Initialize service client (will be created when first needed)
tesla_client: Optional[TeslaMCP] = None

# Create FastMCP server
mcp = FastMCP("tesla-mcp-server")

def get_tesla_client() -> TeslaMCP:
    """Get or create Tesla MCP client."""
    global tesla_client
    if not tesla_client:
        tesla_client = TeslaMCP(auth_manager=tesla_auth)
    return tesla_client

@mcp.tool()
def get_vehicles() -> str:
    """Get list of all vehicles"""
    try:
        async def _get_vehicles():
            client = get_tesla_client()
            return await client.get_vehicles()
        
        vehicles = run_async(_get_vehicles())
        return str(vehicles)
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_vehicle(vehicle_id: str) -> str:
    """Get detailed information about a specific vehicle"""
    try:
        async def _get_vehicle():
            client = get_tesla_client()
            return await client.get_vehicle(vehicle_id)
        
        vehicle_data = run_async(_get_vehicle())
        return str(vehicle_data)
    except Exception as e:
        logger.error(f"Error getting vehicle {vehicle_id}: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def send_command(vehicle_id: str, command: str, parameters: str = "") -> str:
    """Send a command to a vehicle"""
    try:
        async def _send_command():
            client = get_tesla_client()
            params = json.loads(parameters) if parameters else {}
            return await client.send_vehicle_command(vehicle_id, command, params)
        
        result = run_async(_send_command())
        return str(result)
    except Exception as e:
        logger.error(f"Error sending command to vehicle {vehicle_id}: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_solar_system(site_id: str) -> str:
    """Get status of a solar system"""
    try:
        async def _get_solar_system():
            client = get_tesla_client()
            return await client.get_solar_system(site_id)
        
        solar_data = run_async(_get_solar_system())
        return str(solar_data)
    except Exception as e:
        logger.error(f"Error getting solar system {site_id}: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_solar_history(site_id: str, period: str = "day") -> str:
    """Get history of a solar system"""
    try:
        async def _get_solar_history():
            client = get_tesla_client()
            return await client.get_solar_history(site_id, period)
        
        history_data = run_async(_get_solar_history())
        return str(history_data)
    except Exception as e:
        logger.error(f"Error getting solar history for {site_id}: {str(e)}")
        return f"Error: {str(e)}"

@mcp.tool()
def get_system_summary() -> str:
    """Get a summary of all Tesla systems"""
    try:
        async def _get_system_summary():
            client = get_tesla_client()
            return await client.get_system_summary()
        
        summary = run_async(_get_system_summary())
        return str(summary)
    except Exception as e:
        logger.error(f"Error getting system summary: {str(e)}")
        return f"Error: {str(e)}"

# Authentication status tool
@mcp.tool()
def tesla_auth_status() -> str:
    """Check Tesla authentication status"""
    try:
        async def _check_auth():
            try:
                await tesla_auth.get_valid_token()
                return "✅ Authenticated with Tesla API"
            except Exception as e:
                return f"❌ Not authenticated: {str(e)}"
        
        return run_async(_check_auth())
    except Exception as e:
        return f"Error checking authentication: {str(e)}"

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

# Export for mcp run
app = mcp

if __name__ == "__main__":
    main()
