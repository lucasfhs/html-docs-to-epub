#!/usr/bin/env python3
"""Documentation to EPUB Converter - Main entry point."""
from __future__ import annotations

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import main

if __name__ == "__main__":
    main()
