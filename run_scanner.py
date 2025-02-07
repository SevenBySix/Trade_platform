import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(project_root))

from trading_platform.interfaces.cli.scanner_cli import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
