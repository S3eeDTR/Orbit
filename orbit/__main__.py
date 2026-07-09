"""
ORBIT entry point.

Allows the application to be launched using:

    python -m orbit

or, when installed:

    orbit
"""

from .app import run_app


def main() -> None:
    """CLI entry point."""
    run_app()


if __name__ == "__main__":
    main()
