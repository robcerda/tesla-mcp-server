from mcp import TeslaMCP
import json

def handle_tesla_request(request: str) -> str:
    """
    Handle Tesla-related requests from Claude.
    Returns a formatted string response that Claude can understand and relay to the user.
    """
    mcp = TeslaMCP()
    
    try:
        # Get system status
        if "status" in request.lower() or "how are" in request.lower():
            summary = mcp.get_system_summary()
            return format_system_summary(summary)
            
        # Solar system queries
        elif "solar" in request.lower():
            if "history" in request.lower():
                # Get solar history
                systems = mcp.get_solar_systems()
                if not systems:
                    return "No solar systems found."
                site_id = systems[0]['id']
                period = "day"  # default to daily history
                if "week" in request.lower():
                    period = "week"
                elif "month" in request.lower():
                    period = "month"
                elif "year" in request.lower():
                    period = "year"
                history = mcp.get_solar_history(site_id, period)
                return format_solar_history(history, period)
            else:
                # Get current solar status
                systems = mcp.get_solar_systems()
                if not systems:
                    return "No solar systems found."
                site_id = systems[0]['id']
                status = mcp.get_solar_system(site_id)
                return format_solar_status(status)
            
        # Vehicle queries
        elif "vehicle" in request.lower() or "car" in request.lower():
            vehicles = mcp.get_vehicles()
            if not vehicles:
                return "No vehicles found."
            
            # If specific vehicle mentioned
            for vehicle in vehicles:
                if vehicle['display_name'].lower() in request.lower():
                    status = mcp.get_vehicle(vehicle['id'])
                    return format_vehicle_status(status)
            
            # General vehicle status
            return format_vehicles_summary(vehicles)
            
        # Default to system summary if no specific request
        else:
            summary = mcp.get_system_summary()
            return format_system_summary(summary)
            
    except Exception as e:
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

# Example usage
if __name__ == "__main__":
    # Test the handler with some example requests
    test_requests = [
        "What's the status of my Tesla systems?",
        "How's my solar system doing?",
        "What's the solar history for this week?",
        "How's my car doing?",
    ]
    
    for request in test_requests:
        print(f"\nRequest: {request}")
        print("Response:")
        print(handle_tesla_request(request))
        print("-" * 50) 