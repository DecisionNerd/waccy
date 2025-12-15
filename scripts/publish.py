"""Helper script for publishing to PyPI."""

import argparse
import subprocess
import sys
from pathlib import Path


def check_prerequisites() -> tuple[bool, str]:
    """Check if prerequisites are met for publishing."""
    # Check if we're in the project root
    if not Path("pyproject.toml").exists():
        return False, "pyproject.toml not found. Are you in the project root?"

    # Check if uv is available
    result = subprocess.run(
        ["uv", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, "uv is not installed or not in PATH"

    return True, ""


def build_package(clean: bool = False) -> int:
    """Build the package distribution."""
    if clean:
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("Cleaning dist/ directory...")
            import shutil

            shutil.rmtree(dist_dir)

    print("Building package...")
    result = subprocess.run(["uv", "build"], check=False)
    if result.returncode != 0:
        print("❌ Build failed!")
        return result.returncode

    # Verify dist/ directory was created and has files
    dist_dir = Path("dist")
    if not dist_dir.exists() or not list(dist_dir.glob("*")):
        print("❌ Build completed but no distribution files found in dist/")
        return 1

    print("✅ Build successful!")
    dist_files = list(dist_dir.glob("*"))
    print(f"   Created {len(dist_files)} distribution file(s):")
    for file in dist_files:
        print(f"   - {file.name}")
    return 0


def publish_package(
    testpypi: bool = False,
    dry_run: bool = False,
    token: str | None = None,
) -> int:
    """Publish the package to PyPI or TestPyPI."""
    dist_dir = Path("dist")
    if not dist_dir.exists() or not list(dist_dir.glob("*")):
        print("❌ No distribution files found. Run build first.")
        return 1

    if testpypi:
        print("Publishing to TestPyPI...")
        publish_url = "https://test.pypi.org/legacy/"
    else:
        print("Publishing to PyPI...")
        publish_url = "https://upload.pypi.org/legacy/"

    cmd = ["uv", "publish", "--publish-url", publish_url]
    if dry_run:
        cmd.append("--dry-run")
        print("   (DRY RUN - no files will be uploaded)")
    if token:
        cmd.extend(["--token", token])

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print("❌ Publish failed!")
        if not dry_run:
            print("\nNote: Make sure you have:")
            print("  - PyPI/TestPyPI credentials configured")
            print("  - API token set via --token or UV_PUBLISH_TOKEN env var")
            print("  - Or use: uv publish --token pypi-<your-token>")
        return result.returncode

    if dry_run:
        print("✅ Dry run completed successfully!")
    else:
        print("✅ Successfully published!")
        if testpypi:
            print("   Package available at: https://test.pypi.org/project/waccy/")
        else:
            print("   Package available at: https://pypi.org/project/waccy/")
    return 0


def main() -> int:
    """Main entry point for the publish script."""
    parser = argparse.ArgumentParser(
        description="Build and publish WACCY package to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build only
  python scripts/publish.py --build-only

  # Publish to TestPyPI
  python scripts/publish.py --testpypi

  # Dry run (test without uploading)
  python scripts/publish.py --dry-run

  # Full publish with token
  python scripts/publish.py --token pypi-<your-token>

  # Clean build and publish
  python scripts/publish.py --clean
        """,
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build the package, don't publish",
    )
    parser.add_argument(
        "--publish-only",
        action="store_true",
        help="Only publish, skip building (assumes dist/ exists)",
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
        "--clean",
        action="store_true",
        help="Clean dist/ directory before building",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="PyPI API token (or set UV_PUBLISH_TOKEN env var)",
    )

    args = parser.parse_args()

    # Check prerequisites
    ok, error = check_prerequisites()
    if not ok:
        print(f"❌ {error}")
        return 1

    # Build if not publish-only
    if not args.publish_only:
        build_result = build_package(clean=args.clean)
        if build_result != 0:
            return build_result

        if args.build_only:
            print("\n✅ Build complete. Use --publish-only to publish later.")
            return 0

    # Publish
    publish_result = publish_package(
        testpypi=args.testpypi,
        dry_run=args.dry_run,
        token=args.token,
    )
    return publish_result


if __name__ == "__main__":
    sys.exit(main())

