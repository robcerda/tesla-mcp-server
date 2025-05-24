import pytest
from tesla_mcp_server.server import TeslaMCPServer

def test_tesla_mcp_server_instantiation():
    """
    Tests if the TeslaMCPServer can be instantiated.
    This also implicitly tests if the corrected import works.
    """
    try:
        server = TeslaMCPServer()
        assert server is not None, "Server instantiation returned None"
    except ImportError as e:
        pytest.fail(f"Failed to import or instantiate TeslaMCPServer due to ImportError: {e}")
    except Exception as e:
        pytest.fail(f"Failed to instantiate TeslaMCPServer due to an unexpected exception: {e}")
