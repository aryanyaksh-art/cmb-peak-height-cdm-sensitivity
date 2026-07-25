"""Confirm classy is installed and working before anything else runs.

Run this first. If it fails, the problem is the environment, not the physics.
"""

import sys


def main() -> int:
    try:
        import classy
        from classy import Class
    except ImportError as exc:
        print(f"classy import failed: {exc}")
        print("See docs/SETUP_WSL.md.")
        return 1

    version = getattr(classy, "__version__", "unknown")
    print(f"classy version: {version}")
    if version not in ("unknown", "3.3.4.0"):
        print(f"  note: requirements.txt pins 3.3.4.0, found {version}")

    cosmo = Class()
    try:
        cosmo.set({"output": "mPk"})
        cosmo.compute()
        pk = cosmo.pk(0.1, 0)
        print(f"P(k=0.1, z=0) = {pk:.4e}")
        if pk <= 0:
            print("non-positive P(k) -- something is wrong with the build")
            return 1
    finally:
        cosmo.struct_cleanup()
        cosmo.empty()

    for mod in ("numpy", "scipy", "matplotlib"):
        __import__(mod)
        print(f"{mod}: ok")

    print("\nEnvironment looks good.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
