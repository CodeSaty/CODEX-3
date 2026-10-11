#!/usr/bin/env python3
"""Root alias for backend/seed_real_traffic.py"""
import os
import sys

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import seed_real_traffic

if __name__ == "__main__":
    seed_real_traffic.main()
