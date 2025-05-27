from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime
from .auth import TeslaAuth
import sys

class TeslaMCP:
    def __init__(self, auth_manager: TeslaAuth, api_base_url: str = "https://owner-api.teslamotors.com"):
        self.auth_manager = auth_manager
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Tesla Owner API."""
        url = f"{self.api_base_url}{endpoint}"
        token = await self.auth_manager.get_valid_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "TeslaMCP Server"
        }
        # Merge provided headers with default headers, giving priority to provided ones
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        response = await self.client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        try:
            await self.auth_manager.get_valid_token() # Check if auth is working
            return {"status": "healthy", "auth_status": "ok", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"status": "unhealthy", "auth_status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def get_vehicles(self) -> List[Dict[str, Any]]:
        """Get list of all vehicles."""
        try:
            # Use the auth manager's get_vehicles which has the fallback logic
            data = await self.auth_manager.get_vehicles()
            return data.get("response", [])
        except Exception as e:
            print(f"[ERROR] Failed to get vehicles: {str(e)}", file=sys.stderr)
            return []

    async def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Get specific vehicle details."""
        data = await self._make_request("GET", f"/api/1/vehicles/{vehicle_id}")
        return data.get("response", {})

    async def send_vehicle_command(self, vehicle_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a vehicle."""
        # Owner API uses command name in the path
        endpoint = f"/api/1/vehicles/{vehicle_id}/command/{command}"
        return await self._make_request("POST", endpoint, json=parameters or {})

    async def get_solar_systems(self) -> List[Dict[str, Any]]:
        """Get list of all solar systems (energy sites)."""
        data = await self._make_request("GET", "/api/1/products")
        # Filter for energy products
        return [product for product in data.get("response", []) if product.get("resource_type") == "battery"]

    async def get_solar_system(self, site_id: str) -> Dict[str, Any]:
        """Get specific solar system status."""
        data = await self._make_request("GET", f"/api/1/energy_sites/{site_id}/live_status")
        return data.get("response", {})

    async def get_solar_history(self, site_id: str, period: str = "day") -> Dict[str, Any]:
        """Get solar system history."""
        try:
            print(f"[DEBUG] Getting solar history for site {site_id}, period: {period}", file=sys.stderr)
            data = await self._make_request(
                "GET", 
                f"/api/1/energy_sites/{site_id}/calendar_history",
                params={"period": period, "kind": "power"}  # Added kind parameter
            )
            print(f"[DEBUG] Solar history response: {data}", file=sys.stderr)
            return data.get("response", {})
        except Exception as e:
            print(f"[ERROR] Failed to get solar history: {str(e)}", file=sys.stderr)
            if hasattr(e, 'response'):
                print(f"[DEBUG] Response status: {e.response.status_code}", file=sys.stderr)
                print(f"[DEBUG] Response body: {e.response.text}", file=sys.stderr)
            return {}

    async def send_solar_command(self, site_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a solar system."""
        endpoint = f"/api/1/energy_sites/{site_id}/command/{command}"
        return await self._make_request("POST", endpoint, json=parameters or {})

    async def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of all Tesla systems."""
        try:
            print("[DEBUG] Getting vehicles...", file=sys.stderr)
            vehicles = await self.get_vehicles()
            print(f"[DEBUG] Found {len(vehicles)} vehicles", file=sys.stderr)
            
            print("[DEBUG] Getting solar systems...", file=sys.stderr)
            solar_systems = await self.get_solar_systems()
            print(f"[DEBUG] Found {len(solar_systems)} solar systems", file=sys.stderr)

            return {
                "timestamp": datetime.now().isoformat(),
                "vehicles": [
                    {
                        "id": v.get("id"),
                        "name": v.get("display_name"),
                        "state": v.get("state"),
                        "vin": v.get("vin")
                    }
                    for v in vehicles
                ],
                "solar_systems": [
                    {
                        "id": s.get("energy_site_id"),
                        "name": s.get("site_name"),
                        "status": s.get("status"),
                        "total_power": s.get("total_pack_energy"),
                        "battery_level": s.get("percentage_charged")
                    }
                    for s in solar_systems
                ]
            }
        except Exception as e:
            print(f"[ERROR] System summary failed: {str(e)}", file=sys.stderr)
            import traceback
            print(f"[DEBUG] Exception traceback: {traceback.format_exc()}", file=sys.stderr)
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Example usage (commented out as per instructions):
# if __name__ == "__main__":
#     # This part would need an async setup to run, e.g., using asyncio.run()
#     # Also, TeslaAuth needs to be instantiated and passed.
#     # For example:
#     # import asyncio
#     # from .auth import TeslaAuth # Assuming auth.py is in the same directory
#
#     # async def main_async():
#     #     auth = TeslaAuth() # This would need .env setup for client_id/secret
#     #     # You might need to load .env here if auth doesn't do it or does it relatively
#     #     # from dotenv import load_dotenv
#     #     # load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
# 
#     #     mcp = TeslaMCP(auth_manager=auth)
#     #
#     #     # Get system summary
#     #     summary = await mcp.get_system_summary()
#     #     print(json.dumps(summary, indent=2))
#     #
#     #     # Example: Get solar system status
#     #     if summary.get("solar_systems") and summary["solar_systems"]:
#     #         site_id = summary["solar_systems"][0]["id"]
#     #         if site_id: # Ensure site_id is not None
#     #             solar_status = await mcp.get_solar_system(site_id)
#     #             print("\nSolar System Status:")
#     #             print(json.dumps(solar_status, indent=2))
#     #
#     #     # Example: Get vehicle status
#     #     if summary.get("vehicles") and summary["vehicles"]:
#     #         vehicle_id = summary["vehicles"][0]["id"]
#     #         if vehicle_id: # Ensure vehicle_id is not None
#     #             vehicle_status = await mcp.get_vehicle(vehicle_id)
#     #             print("\nVehicle Status:")
#     #             print(json.dumps(vehicle_status, indent=2))
#
#     # if __name__ == "__main__":
#     #    asyncio.run(main_async())