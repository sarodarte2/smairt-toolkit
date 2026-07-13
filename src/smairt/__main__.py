"""Allow `python -m smairt` to invoke the same public CLI as `smairt`."""

from smairt.cli import app

if __name__ == "__main__":
    app()
