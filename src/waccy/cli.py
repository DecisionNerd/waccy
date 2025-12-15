"""Command-line interface for WACCY."""

import sys
from typing import Optional


def main(args: Optional[list[str]] = None) -> int:
    """Main CLI entry point."""
    if args is None:
        args = sys.argv[1:]

    # TODO: Implement CLI commands
    # - waccy extract <source> [options]
    # - waccy model <type> [options]
    # - waccy classify [options]
    # - waccy export <model> [options]

    print("WACCY CLI - Coming soon!")
    print("Use the Python API for now:")
    print("  from waccy.extraction import ExtractorRegistry")
    print("  from waccy.modeling import ModelBuilder")

    return 0


if __name__ == "__main__":
    sys.exit(main())

