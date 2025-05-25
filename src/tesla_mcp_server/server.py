from mcp_server import MCPServer, MCPRequest, MCPResponse # Assuming mcp_server is a provided library
from typing import Dict, Any, List
import os
import asyncio # Added asyncio
from pathlib import Path # Added Path
from python_dotenv import load_dotenv, find_dotenv # Switched to python_dotenv

from .auth import TeslaAuth
from .mcp import TeslaMCP

# Load .env from project root for server-specific configurations
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = find_dotenv(str(PROJECT_ROOT / ".env"), usecwd=True) or PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=DOTENV_PATH) # TeslaAuth will also load .env, this is fine.

TESLA_API_BASE_URL = os.getenv("TESLA_API_BASE_URL", "https://fleet-api.prd.na.vn.cloud.tesla.com")
if not TESLA_API_BASE_URL: # Ensure it's set
    raise ValueError("TESLA_API_BASE_URL must be set in .env or have a default in code.")


class TeslaMCPServer(MCPServer):
    def __init__(self):
        super().__init__()
        # TeslaAuth handles its own .env loading for ENCRYPTION_KEY and credentials
        self.auth_manager = TeslaAuth() 
        self.tesla_mcp = TeslaMCP(auth_manager=self.auth_manager, api_base_url=TESLA_API_BASE_URL)

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP requests."""
        try:
            # Get system status
            if "status" in request.text.lower() or "how are" in request.text.lower():
                summary = await self.tesla_mcp.get_system_summary()
                return MCPResponse(text=format_system_summary(summary))
                
            # Solar system queries
            elif "solar" in request.text.lower():
                if "history" in request.text.lower():
                    # Get solar history
                    systems = await self.tesla_mcp.get_solar_systems()
                    if not systems:
                        return MCPResponse(text="No solar systems found.")
                    # Assuming the first solar system if multiple exist for simplicity
                    site_id = systems[0].get('id', systems[0].get('energy_site_id')) # Adjusted to match mcp.py summary logic
                    if not site_id:
                         return MCPResponse(text="Could not determine site ID for the solar system.")
                    period = "day"  # default to daily history
                    if "week" in request.text.lower():
                        period = "week"
                    elif "month" in request.text.lower():
                        period = "month"
                    elif "year" in request.text.lower():
                        period = "year"
                    history = await self.tesla_mcp.get_solar_history(site_id, period)
                    return MCPResponse(text=format_solar_history(history, period))
                else:
                    # Get current solar status
                    systems = await self.tesla_mcp.get_solar_systems()
                    if not systems:
                        return MCPResponse(text="No solar systems found.")
                    site_id = systems[0].get('id', systems[0].get('energy_site_id'))
                    if not site_id:
                         return MCPResponse(text="Could not determine site ID for the solar system.")
                    status = await self.tesla_mcp.get_solar_system(site_id)
                    return MCPResponse(text=format_solar_status(status))
                
            # Vehicle queries
            elif "vehicle" in request.text.lower() or "car" in request.text.lower():
                vehicles = await self.tesla_mcp.get_vehicles()
                if not vehicles:
                    return MCPResponse(text="No vehicles found.")
                
                # If specific vehicle mentioned
                for vehicle in vehicles:
                    vehicle_name = vehicle.get('display_name', vehicle.get('vehicle_name'))
                    vehicle_id = vehicle.get('id', vehicle.get('id_s'))
                    if not vehicle_name or not vehicle_id:
                        continue # Skip if essential info missing

                    if vehicle_name.lower() in request.text.lower():
                        status = await self.tesla_mcp.get_vehicle(vehicle_id)
                        return MCPResponse(text=format_vehicle_status(status))
                
                # General vehicle status
                return MCPResponse(text=format_vehicles_summary(vehicles))
                
            # Default to system summary if no specific request
            else:
                summary = await self.tesla_mcp.get_system_summary()
                return MCPResponse(text=format_system_summary(summary))
                
        except Exception as e:
            # Log the full error for debugging
            print(f"Error handling request: {e}") 
            import traceback
            traceback.print_exc()
            return MCPResponse(text=f"Error: {str(e)}")

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

if __name__ == "__main__":
    server = TeslaMCPServer()
    server.run()
