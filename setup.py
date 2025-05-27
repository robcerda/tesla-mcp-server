from setuptools import setup, find_packages

setup(
    name="tesla-mcp-server",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "httpx",
        "click",
        "python-dotenv",
        "cryptography",
        "mcp[cli]"
    ],
    entry_points={
        "console_scripts": [
            "tesla-mcp=tesla_mcp_server.cli:cli",
        ],
    },
    python_requires=">=3.7",
) 