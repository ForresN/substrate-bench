"""Enable `python -m substrate_bench run ...` (mirrors the console script)."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
