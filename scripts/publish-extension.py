"""Publish a specific extension package to PyPI."""

import argparse
import subprocess
import sys
from pathlib import Path


def publish_extension(
    extension_name: str,
    testpypi: bool = False,
    dry_run: bool = False,
    token: str | None = None,
) -> int:
    """Publish an extension package to PyPI."""
    extension_dir = Path("extensions") / extension_name
    if not extension_dir.exists():
        print(f"❌ Extension directory not found: {extension_dir}")
        return 1

    dist_dir = extension_dir / "dist"
    if not dist_dir.exists() or not list(dist_dir.glob("*")):
        print(f"❌ No distribution files found. Build first with:")
        print(f"   python scripts/build-extension.py {extension_name}")
        return 1

    if testpypi:
        print(f"Publishing {extension_name} to TestPyPI...")
        publish_url = "https://test.pypi.org/legacy/"
    else:
        print(f"Publishing {extension_name} to PyPI...")
        publish_url = "https://upload.pypi.org/legacy/"

    cmd = ["uv", "publish", "--publish-url", publish_url]
    if dry_run:
        cmd.append("--dry-run")
        print("   (DRY RUN - no files will be uploaded)")
    if token:
        cmd.extend(["--token", token])

    result = subprocess.run(cmd, cwd=extension_dir, check=False)
    if result.returncode != 0:
        print(f"❌ Publish failed for {extension_name}!")
        if not dry_run:
            print("\nNote: Make sure you have:")
            print("  - PyPI/TestPyPI credentials configured")
            print("  - API token set via --token or UV_PUBLISH_TOKEN env var")
        return result.returncode

    if dry_run:
        print(f"✅ Dry run completed successfully for {extension_name}!")
    else:
        print(f"✅ Successfully published {extension_name}!")
        if testpypi:
            print(f"   Package available at: https://test.pypi.org/project/{extension_name}/")
        else:
            print(f"   Package available at: https://pypi.org/project/{extension_name}/")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Publish a WACCY extension package to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish to TestPyPI
  python scripts/publish-extension.py waccy-quickbooks --testpypi

  # Dry run
  python scripts/publish-extension.py waccy-edgar --dry-run

  # Full publish with token
  python scripts/publish-extension.py waccy-quickbooks --token pypi-<your-token>
        """,
    )
    parser.add_argument(
        "extension",
        help="Extension name (e.g., waccy-quickbooks, waccy-edgar)",
    )
    parser.add_argument(
        "--testpypi",
        action="store_true",
        help="Publish to TestPyPI instead of PyPI",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actually uploading",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="PyPI API token (or set UV_PUBLISH_TOKEN env var)",
    )

    args = parser.parse_args()

    return publish_extension(
        args.extension,
        testpypi=args.testpypi,
        dry_run=args.dry_run,
        token=args.token,
    )


if __name__ == "__main__":
    sys.exit(main())

