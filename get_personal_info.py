# main.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("getpersonalinfo")
@mcp.tool()
async def get_personal_info(name:str) -> dict:
    """Get the city of person based on the name."""
    try:

        match(name):
            case "An":
                info = "An lives in New York city"
            case "Thạch":
                info = "Thach lives in London city"
            case "Hùng":
                info = "Hung lives in Paris city"
            case _:
                return {"error": "Invalid name"}
        
        return info
    except Exception as e:
        return {"error": str(e)}
if __name__ == "__main__":
    print("Fetch personal Data MCP Server is running...")
    mcp.run()
