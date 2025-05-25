"""Main entry point for the Tesla MCP Server."""

from .server import mcp

def main():
    """Run the Tesla MCP Server."""
    mcp.run()

if __name__ == "__main__":
    main() 