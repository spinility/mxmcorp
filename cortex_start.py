#!/usr/bin/env python3
"""
Cortex Startup Script

Beautiful entry point for Cortex MXMCorp
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from cortex.cli.cortex_cli import main

if __name__ == "__main__":
    main()
