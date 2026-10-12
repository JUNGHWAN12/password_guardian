"""Source checkout entry point; paths are independent of the working directory."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from password_guardian.__main__ import main

if __name__ == "__main__":
    main()
