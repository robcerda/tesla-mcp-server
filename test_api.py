import asyncio
import json
from tesla_mcp_server.auth import TeslaAuth
from tesla_mcp_server.mcp import TeslaMCP

async def test_api():
    try:
        # Initialize auth and MCP
        print("Initializing TeslaAuth...")
        auth = TeslaAuth()
        
        print("Initializing TeslaMCP...")
        mcp = TeslaMCP(auth_manager=auth)
        
        # Test health check
        print("\nTesting health check...")
        health = await mcp.get_health()
        print(json.dumps(health, indent=2))
        
        # Get system summary
        print("\nGetting system summary...")
        summary = await mcp.get_system_summary()
        print(json.dumps(summary, indent=2))
        
        # Test vehicle endpoints if vehicles exist
        if summary.get("vehicles"):
            vehicle_id = summary["vehicles"][0]["id"]
            print(f"\nTesting vehicle endpoints for vehicle {vehicle_id}...")
            
            # Get vehicle details
            vehicle = await mcp.get_vehicle(vehicle_id)
            print("\nVehicle details:")
            print(json.dumps(vehicle, indent=2))
            
            # Test a simple command (e.g., flash lights)
            print("\nTesting flash_lights command...")
            try:
                result = await mcp.send_vehicle_command(vehicle_id, "flash_lights")
                print(json.dumps(result, indent=2))
            except Exception as e:
                print(f"Command failed: {str(e)}")
        
        # Test solar endpoints if solar systems exist
        if summary.get("solar_systems"):
            site_id = summary["solar_systems"][0]["id"]
            print(f"\nTesting solar endpoints for site {site_id}...")
            
            # Get solar system status
            solar_status = await mcp.get_solar_system(site_id)
            print("\nSolar system status:")
            print(json.dumps(solar_status, indent=2))
            
            # Get solar history
            print("\nGetting solar history...")
            history = await mcp.get_solar_history(site_id)
            print(json.dumps(history, indent=2))
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_api()) 