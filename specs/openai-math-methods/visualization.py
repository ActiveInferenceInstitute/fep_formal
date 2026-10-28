"""Project the installed visual methods from validated checkout positioning sources.

--check compares JSON, HTML and every SVG without repairing retained artifacts.
All numerical evaluations remain explanatory, neither proof nor empirical evidence.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

if __name__ == "__main__":
    sys.dont_write_bytecode = True

from fep_formal.methods import build_mathematical_positioning
from fep_formal.methods.visualization import (
    build_visual_model,
    projection_bytes,
)

HERE = Path(__file__).resolve().parent


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if sys.version_info[:2] != (3, 14):
        parser.error("repository validator requires Python 3.14")
    try:
        outputs = projection_bytes(
            build_visual_model(
                build_mathematical_positioning(HERE.parents[1]).as_dict()
            )
        )
        if args.check:
            stale = [
                str(path)
                for path, data in outputs.items()
                if not (HERE / path).is_file() or (HERE / path).read_bytes() != data
            ]
            if stale:
                raise ValueError("visual artifact drift: " + ", ".join(stale))
            print("visual analysis artifacts current; no proof or empirical acceptance")
        else:
            for path, data in outputs.items():
                (HERE / path).parent.mkdir(parents=True, exist_ok=True)
                (HERE / path).write_bytes(data)
            print(
                "wrote offline visual analysis artifacts; no proof or empirical acceptance"
            )
        return 0
    except (ValueError, OSError) as exc:
        print("visual analysis failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
