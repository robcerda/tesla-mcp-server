import asyncio
import json
import click
from pathlib import Path
from .auth import TeslaAuth
from .mcp import TeslaMCP

@click.group()
def cli():
    """Tesla MCP CLI - Control your Tesla vehicles and solar systems."""
    pass

@cli.command()
def status():
    """Get status of all Tesla systems."""
    async def get_status():
        auth = TeslaAuth()
        mcp = TeslaMCP(auth_manager=auth)
        
        try:
            summary = await mcp.get_system_summary()
            print(json.dumps(summary, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(get_status())

@cli.command()
@click.argument('vehicle_id')
def vehicle(vehicle_id):
    """Get detailed information about a specific vehicle."""
    async def get_vehicle():
        auth = TeslaAuth()
        mcp = TeslaMCP(auth_manager=auth)
        
        try:
            vehicle_data = await mcp.get_vehicle(vehicle_id)
            print(json.dumps(vehicle_data, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(get_vehicle())

@cli.command()
@click.argument('vehicle_id')
@click.argument('command')
@click.option('--params', help='JSON string of command parameters')
def command(vehicle_id, command, params):
    """Send a command to a vehicle."""
    async def send_command():
        auth = TeslaAuth()
        mcp = TeslaMCP(auth_manager=auth)
        
        try:
            parameters = json.loads(params) if params else {}
            result = await mcp.send_vehicle_command(vehicle_id, command, parameters)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(send_command())

@cli.command()
@click.argument('site_id')
def solar(site_id):
    """Get status of a solar system."""
    async def get_solar():
        auth = TeslaAuth()
        mcp = TeslaMCP(auth_manager=auth)
        
        try:
            solar_data = await mcp.get_solar_system(site_id)
            print(json.dumps(solar_data, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(get_solar())

@cli.command()
@click.argument('site_id')
@click.option('--period', default='day', help='Time period for history (day/week/month/year)')
def history(site_id, period):
    """Get history of a solar system."""
    async def get_history():
        auth = TeslaAuth()
        mcp = TeslaMCP(auth_manager=auth)
        
        try:
            history_data = await mcp.get_solar_history(site_id, period)
            print(json.dumps(history_data, indent=2))
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(get_history())

if __name__ == '__main__':
    cli() 