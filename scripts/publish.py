"""Helper script for publishing to PyPI."""

import subprocess
import sys


def main() -> int:
    """Build and publish package to PyPI."""
    print("Building package...")
    result = subprocess.run(["uv", "build"], check=False)
    if result.returncode != 0:
        print("Build failed!")
        return result.returncode

    print("Publishing to PyPI...")
    result = subprocess.run(["uv", "publish"], check=False)
    if result.returncode != 0:
        print("Publish failed!")
        return result.returncode

    print("Successfully published!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

