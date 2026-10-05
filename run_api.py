#!/usr/bin/env python3
import sys
from pathlib import Path

# Explicitly add current directory to sys.path
root_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(root_dir))

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8090)
