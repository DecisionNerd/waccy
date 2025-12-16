"""Build a specific extension package."""

import argparse
import subprocess
import sys
from pathlib import Path


def build_extension(extension_name: str, clean: bool = False) -> int:
    """Build an extension package."""
    extension_dir = Path("extensions") / extension_name
    if not extension_dir.exists():
        print(f"❌ Extension directory not found: {extension_dir}")
        return 1

    pyproject = extension_dir / "pyproject.toml"
    if not pyproject.exists():
        print(f"❌ pyproject.toml not found in {extension_dir}")
        return 1

    if clean:
        dist_dir = extension_dir / "dist"
        if dist_dir.exists():
            print(f"Cleaning {dist_dir}...")
            import shutil

            shutil.rmtree(dist_dir)

    print(f"Building {extension_name}...")
    result = subprocess.run(
        ["uv", "build"],
        cwd=extension_dir,
        check=False,
    )
    if result.returncode != 0:
        print(f"❌ Build failed for {extension_name}!")
        return result.returncode

    # Verify dist/ directory was created
    dist_dir = extension_dir / "dist"
    if not dist_dir.exists() or not list(dist_dir.glob("*")):
        print(f"❌ Build completed but no distribution files found for {extension_name}")
        return 1

    print(f"✅ Build successful for {extension_name}!")
    dist_files = list(dist_dir.glob("*"))
    print(f"   Created {len(dist_files)} distribution file(s):")
    for file in dist_files:
        print(f"   - {file.name}")

    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build a WACCY extension package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build waccy-quickbooks
  python scripts/build-extension.py waccy-quickbooks

  # Build waccy-edgar
  python scripts/build-extension.py waccy-edgar

  # Clean build
  python scripts/build-extension.py waccy-quickbooks --clean
        """,
    )
    parser.add_argument(
        "extension",
        help="Extension name (e.g., waccy-quickbooks, waccy-edgar)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean dist/ directory before building",
    )

    args = parser.parse_args()

    return build_extension(args.extension, clean=args.clean)


if __name__ == "__main__":
    sys.exit(main())

