from typing import Dict, Any, List, Optional
import httpx
import json
from datetime import datetime
from .auth import TeslaAuth

class TeslaMCP:
    def __init__(self, auth_manager: TeslaAuth, api_base_url: str = "https://fleet-api.prd.na.vn.cloud.tesla.com"):
        self.auth_manager = auth_manager
        self.api_base_url = api_base_url
        self.client = httpx.AsyncClient()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Tesla Fleet API."""
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
        """Get server health status (Note: This is a conceptual local health check, not a Tesla API endpoint)."""
        # This method might need to be re-evaluated as it's not a standard Tesla API call.
        # For now, it could return the status of the auth manager or a simple OK.
        # Or, if there's a Tesla API status endpoint, it could be used here.
        # Let's assume it's a local check for now or a dummy.
        try:
            await self.auth_manager.get_valid_token() # Check if auth is working
            return {"status": "healthy", "auth_status": "ok", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"status": "unhealthy", "auth_status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def get_vehicles(self) -> List[Dict[str, Any]]:
        """Get list of all vehicles."""
        # The Tesla API returns a response object with a 'response' key containing the list
        data = await self._make_request("GET", "/api/1/vehicles")
        return data.get("response", [])

    async def get_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        """Get specific vehicle details."""
        # The Tesla API returns a response object with a 'response' key containing the vehicle data
        data = await self._make_request("GET", f"/api/1/vehicles/{vehicle_id}")
        return data.get("response", {})

    async def send_vehicle_command(self, vehicle_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a vehicle."""
        # The command name itself is usually part of the path for Tesla vehicle commands
        # e.g., /api/1/vehicles/{vehicle_id}/command/honk_horn
        # However, the original mcp.py used a generic /commands endpoint and put command in body.
        # Let's stick to the provided task: /api/1/vehicles/{vehicle_id}/command and command in body.
        request_body = {"command": command} # This is a deviation from typical Tesla API
        if parameters:
            request_body.update(parameters) # Merging parameters into the main body if any.
                                            # Or, if parameters should be nested: request_body["parameters"] = parameters
                                            # Given the original structure, let's assume it's flat for now or command specific.
                                            # The original code was: data = {"command": command, "parameters": parameters or {}}
                                            # This is ambiguous. Let's assume 'parameters' are key-value pairs for the command itself.
                                            # For example, for set_temps, parameters might be {"driver_temp": 20, "passenger_temp": 20}
                                            # The Tesla API usually has specific endpoints like /command/set_temps and expects JSON body for those params.
                                            # Reverting to the original structure of the data payload.
        data_payload = {"command_name": command, **(parameters or {})} # Using command_name to avoid clash if 'command' is a parameter
                                                                    # Or, if the API expects `{"command": "the_command", "param1": "value1"}`
                                                                    # Let's use the original structure from `send_vehicle_command`
        data_payload_original = {"command": command, "parameters": parameters or {}}
        # The actual Tesla API for sending commands is typically like:
        # POST /api/1/vehicles/{vehicle_id}/command/{command_name}
        # with an optional JSON body for parameters if the command requires them.
        # The prompt asks for `/api/1/vehicles/{vehicle_id}/command` with command in body.
        # This is unusual for Tesla. Let's assume `parameters` are the actual body for the command.
        # Example: command="honk_horn", parameters={}
        # Example: command="set_temps", parameters={"driver_temp":20, "passenger_temp":20}
        # The prompt is: `send_vehicle_command(self, vehicle_id: str, command: str, parameters: Optional[Dict[str, Any]] = None)`
        # and `data = {"command": command, "parameters": parameters or {}}`
        # and endpoint `/api/1/vehicles/{vehicle_id}/command`
        # This implies the server at `/api/1/vehicles/{vehicle_id}/command` will parse the `command` field from the JSON body.
        return await self._make_request("POST", f"/api/1/vehicles/{vehicle_id}/command", json=data_payload_original)

    async def get_solar_systems(self) -> List[Dict[str, Any]]:
        """Get list of all solar systems (energy sites)."""
        # Using /api/1/products as per some documentation, then filter for ENERGY_SITES
        # Or /api/1/energy_sites if that's preferred by the prompt. Prompt suggested /api/1/energy_sites.
        data = await self._make_request("GET", "/api/1/energy_sites")
        return data.get("response", []) # Assuming response structure similar to vehicles

    async def get_solar_system(self, site_id: str) -> Dict[str, Any]:
        """Get specific solar system status (live status)."""
        data = await self._make_request("GET", f"/api/1/energy_sites/{site_id}/live_status")
        return data.get("response", {})

    async def get_solar_history(self, site_id: str, period: str = "day") -> Dict[str, Any]:
        """Get solar system history."""
        # The Tesla API for energy history is usually /api/1/energy_sites/{energy_site_id}/calendar_history
        # or /api/1/energy_sites/{site_id}/history?period={period} as per prompt.
        data = await self._make_request("GET", f"/api/1/energy_sites/{site_id}/history", params={"period": period})
        return data.get("response", {})

    async def send_solar_command(self, site_id: str, command: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a command to a solar system."""
        # Similar to vehicle commands, command might be in path or body.
        # Following the pattern from send_vehicle_command based on prompt.
        data_payload = {"command": command, "parameters": parameters or {}}
        return await self._make_request("POST", f"/api/1/energy_sites/{site_id}/command", json=data_payload)

    async def get_system_summary(self) -> Dict[str, Any]:
        """Get a summary of all Tesla systems."""
        try:
            vehicles = await self.get_vehicles()
            solar_systems = await self.get_solar_systems()

            return {
                "timestamp": datetime.now().isoformat(),
                "vehicles": [
                    {
                        "id": v.get("id_s", v.get("id")),
                        "name": v.get("display_name", v.get("vehicle_name")),
                        "state": v.get("state"),
                        "battery_level": v.get("charge_state", {}).get("battery_level") if v.get("charge_state") else v.get("battery_level")
                    }
                    for v in vehicles
                ],
                "solar_systems": [
                    {
                        "id": s.get("energy_site_id", s.get("id")),
                        "name": s.get("site_name"),
                        "status": s.get("status"),
                        "total_power": s.get("total_pack_energy"),
                        "battery_level": s.get("percentage_charged")
                    }
                    for s in solar_systems
                ]
            }
        except Exception as e:
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