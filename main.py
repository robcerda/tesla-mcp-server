from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
from auth import TeslaAuth

# Load environment variables from .env file in project root
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="Tesla MCP Server")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tesla API configuration
TESLA_API_BASE = "https://fleet-api.prd.na.vn.cloud.tesla.com"

# Models
class Vehicle(BaseModel):
    id: str
    vin: str
    display_name: str
    state: str
    battery_level: Optional[float]
    last_seen: Optional[datetime]

class Command(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None

class SolarSystem(BaseModel):
    id: str
    site_name: str
    status: str
    total_power: Optional[float]  # Current power generation in watts
    energy_today: Optional[float]  # Energy generated today in kWh
    energy_lifetime: Optional[float]  # Total energy generated in kWh
    grid_power: Optional[float]  # Power flowing to/from grid in watts
    battery_power: Optional[float]  # Power flowing to/from battery in watts
    load_power: Optional[float]  # Power being used by the home in watts
    battery_level: Optional[float]  # Battery charge percentage
    last_seen: Optional[datetime]

class SolarCommand(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None

# Authentication
tesla_auth = TeslaAuth()

async def get_tesla_client():
    # Configure the client with DNS settings and timeouts
    async with httpx.AsyncClient(
        timeout=30.0,
        verify=True,  # Enable SSL verification
        follow_redirects=True,
        headers={
            "Accept": "application/json",
            "User-Agent": "TeslaMCP/1.0"
        },
        # Add DNS settings
        trust_env=True,  # Use system DNS settings
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        # Add DNS resolver configuration
        transport=httpx.AsyncHTTPTransport(
            retries=3,
            verify=True,
            trust_env=True
        )
    ) as client:
        try:
            # Test DNS resolution
            print(f"Testing DNS resolution for {TESLA_API_BASE}")
            await client.get(f"{TESLA_API_BASE}/health")
            print("DNS resolution successful")
        except Exception as e:
            print(f"DNS resolution test failed: {str(e)}")
            # Continue anyway as the actual requests might still work
        yield client

async def get_valid_token():
    return await tesla_auth.get_valid_token()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Vehicle endpoints
@app.get("/vehicles", response_model=List[Vehicle])
async def list_vehicles(token: str = Depends(get_valid_token), client: httpx.AsyncClient = Depends(get_tesla_client)):
    try:
        print(f"Making request to {TESLA_API_BASE}/api/1/vehicles")
        print(f"Using token: {token[:10]}...")
        
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/vehicles",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        return [Vehicle(**vehicle) for vehicle in data.get("response", [])]
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, "response"):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vehicles/{vehicle_id}", response_model=Vehicle)
async def get_vehicle(
    vehicle_id: str,
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        print(f"Making request to {TESLA_API_BASE}/api/1/vehicles/{vehicle_id}")
        print(f"Using token: {token[:10]}...")
        
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/vehicles/{vehicle_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        return Vehicle(**data.get("response", {}))
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, "response"):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/vehicles/{vehicle_id}/commands")
async def send_command(
    vehicle_id: str,
    command: Command,
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        response = await client.post(
            f"{TESLA_API_BASE}/api/1/vehicles/{vehicle_id}/command/{command.command}",
            headers={"Authorization": f"Bearer {token}"},
            json=command.parameters or {}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))

# Solar endpoints
@app.get("/solar", response_model=List[SolarSystem])
async def list_solar_systems(token: str = Depends(get_valid_token), client: httpx.AsyncClient = Depends(get_tesla_client)):
    try:
        # First get the site ID
        print(f"Making request to {TESLA_API_BASE}/api/1/energy_sites")
        print(f"Using token: {token[:10]}...")
        
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/energy_sites",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # If we have a site ID, get the detailed data for each site
        sites = []
        for site in data.get("response", []):
            site_id = site.get("id")
            if site_id:
                site_response = await client.get(
                    f"{TESLA_API_BASE}/api/1/energy_sites/{site_id}",
                    headers={
                        "Authorization": f"Bearer {token}"
                    }
                )
                site_response.raise_for_status()
                site_data = site_response.json()
                sites.append(SolarSystem(**site_data.get("response", {})))
        
        return sites
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, "response"):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/solar/{site_id}", response_model=SolarSystem)
async def get_solar_system(
    site_id: str,
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        print(f"Making request to {TESLA_API_BASE}/api/1/energy_sites/{site_id}/live_status")
        print(f"Using token: {token[:10]}...")
        
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/energy_sites/{site_id}/live_status",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        return SolarSystem(**data.get("response", {}))
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, "response"):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/solar/{site_id}/commands")
async def send_solar_command(
    site_id: str,
    command: SolarCommand,
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        response = await client.post(
            f"{TESLA_API_BASE}/api/1/energy_sites/{site_id}/command/{command.command}",
            headers={"Authorization": f"Bearer {token}"},
            json=command.parameters or {}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))

@app.get("/solar/{site_id}/history")
async def get_solar_history(
    site_id: str,
    period: str = "day",  # day, week, month, year
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/energy_sites/{site_id}/history",
            params={"period": period},
            headers={"Authorization": f"Bearer {token}"}
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))

@app.get("/solar/{site_id}/telemetry")
async def get_solar_telemetry(
    site_id: str,
    kind: str = "charge",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    time_zone: str = "UTC",
    token: str = Depends(get_valid_token),
    client: httpx.AsyncClient = Depends(get_tesla_client)
):
    try:
        params = {
            "kind": kind,
            "time_zone": time_zone
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        print(f"Making request to {TESLA_API_BASE}/api/1/energy_sites/{site_id}/telemetry_history")
        print(f"Using token: {token[:10]}...")
        print(f"With params: {params}")
        
        response = await client.get(
            f"{TESLA_API_BASE}/api/1/energy_sites/{site_id}/telemetry_history",
            params=params,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"HTTP Error: {str(e)}")
        if hasattr(e, "response"):
            print(f"Error response: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code if hasattr(e, "response") else 500,
                          detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 