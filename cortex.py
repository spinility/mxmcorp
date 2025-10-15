#!/usr/bin/env python3
"""
Cortex MXMCorp - CLI Principal
Interface conversationnelle intelligente

Usage:
    python cortex.py
    ou après installation: cortex
"""

import sys
import os

# Ajouter le dossier au path pour imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cortex.cli.main import main

if __name__ == "__main__":
    main()
