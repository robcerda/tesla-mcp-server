"""Main entry point for the Tesla MCP Server."""

from .server import TeslaMCPServer

def main():
    """Run the Tesla MCP Server."""
    server = TeslaMCPServer()
    server.run()

if __name__ == "__main__":
    main() 