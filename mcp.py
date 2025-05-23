from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime

class TeslaMCP:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Tesla MCP server."""
        url = f"{self.base_url}{endpoint}"
        response = self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        return self._make_request("GET", "/health")

    def get_vehicles(self) -> List[Dict[str, Any]]:
        """Get list of all vehicles."""
        return self._make_request("GET", "/vehicles")

    def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Get specific vehicle details."""
        return self._make_request("GET", f"/vehicles/{vehicle_id}")

    def send_vehicle_command(self, vehicle_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a vehicle."""
        data = {"command": command, "parameters": parameters or {}}
        return self._make_request("POST", f"/vehicles/{vehicle_id}/commands", json=data)

    def get_solar_systems(self) -> List[Dict[str, Any]]:
        """Get list of all solar systems."""
        return self._make_request("GET", "/solar")

    def get_solar_system(self, site_id: str) -> Dict[str, Any]:
        """Get specific solar system status."""
        return self._make_request("GET", f"/solar/{site_id}")

    def get_solar_history(self, site_id: str, period: str = "day") -> Dict[str, Any]:
        """Get solar system history."""
        return self._make_request("GET", f"/solar/{site_id}/history", params={"period": period})

    def send_solar_command(self, site_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a solar system."""
        data = {"command": command, "parameters": parameters or {}}
        return self._make_request("POST", f"/solar/{site_id}/commands", json=data)

    def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of all Tesla systems."""
        try:
            vehicles = self.get_vehicles()
            solar_systems = self.get_solar_systems()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "vehicles": [
                    {
                        "id": v["id"],
                        "name": v["display_name"],
                        "state": v["state"],
                        "battery_level": v.get("battery_level")
                    }
                    for v in vehicles
                ],
                "solar_systems": [
                    {
                        "id": s["id"],
                        "name": s["site_name"],
                        "status": s["status"],
                        "total_power": s.get("total_power"),
                        "battery_level": s.get("battery_level")
                    }
                    for s in solar_systems
                ]
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Example usage:
if __name__ == "__main__":
    mcp = TeslaMCP()
    
    # Get system summary
    summary = mcp.get_system_summary()
    print(json.dumps(summary, indent=2))
    
    # Example: Get solar system status
    if summary.get("solar_systems"):
        site_id = summary["solar_systems"][0]["id"]
        solar_status = mcp.get_solar_system(site_id)
        print("\nSolar System Status:")
        print(json.dumps(solar_status, indent=2))
    
    # Example: Get vehicle status
    if summary.get("vehicles"):
        vehicle_id = summary["vehicles"][0]["id"]
        vehicle_status = mcp.get_vehicle(vehicle_id)
        print("\nVehicle Status:")
        print(json.dumps(vehicle_status, indent=2)) 