# main.py
from mcp.server.fastmcp import FastMCP
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OPEN_WEATHER_API_KEY = os.getenv('OPEN_WEATHER_MAP_API_KEY')

mcp = FastMCP("gettemperature")
@mcp.tool()
async def get_temperature_data(location:str) -> dict:
    """Fetch real-time temperature data by location."""
    URL = f"https://api.openweathermap.org/data/2.5/weather?q={location}&APPID={OPEN_WEATHER_API_KEY}"
    try:
        response = requests.get(URL)
        print(response)
        return response.json()
    except Exception as e:
        return {"error": str(e)}
if __name__ == "__main__":
    print("Temperature Data MCP Server is running...")
    mcp.run()
