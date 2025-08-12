import os
import unittest
from pathlib import Path

def main() -> None:
    # Resolve repository root from this file location
    repo_root: Path = Path(__file__).resolve().parent

    # Ensure imports resolve to the local package by running from repo root
    os.chdir(repo_root)

    # Use unittest discovery with clear, explicit arguments
    discover_args = [
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "tests_*.py",
        "-v",
    ]

    unittest.main(module=None, argv=discover_args)


if __name__ == "__main__":
    main()


