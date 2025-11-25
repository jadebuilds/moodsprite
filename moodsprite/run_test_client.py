#!/usr/bin/env python3
"""
Run the Moodsprite gRPC test client.

This script provides a convenient way to run the test client from the moodsprite package root.
"""

import sys
import os

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from test_client import main

if __name__ == "__main__":
    main()
