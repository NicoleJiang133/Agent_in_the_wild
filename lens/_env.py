"""Small env-var helpers shared across agents."""
import os


def require(name: str) -> str:
    """Return an env var, or raise a friendly error if it's missing or empty."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Add it to .env at the repo root, "
            f"then restart your kernel or shell."
        )
    return value
