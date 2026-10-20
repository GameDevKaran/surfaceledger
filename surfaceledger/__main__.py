import argparse
import json
from pathlib import Path
import sys

from .pipeline import InputError, analyze, require_opencv5


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect source-backed planar capture coverage using OpenCV 5.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("analyze")
    run.add_argument("capture_set", type=Path)
    run.add_argument("--output", required=True, type=Path)
    fixture = sub.add_parser("fixtures")
    fixture.add_argument("--output", required=True, type=Path)
    sub.add_parser("version")
    args = parser.parse_args()
    try:
        if args.command == "version":
            print(json.dumps(require_opencv5()))
        elif args.command == "fixtures":
            from .fixtures import generate
            print(json.dumps(generate(args.output)))
        else:
            result = analyze(args.capture_set, args.output)
            print(json.dumps({"report": str(args.output / "report.json"), **result["summary"]}))
        return 0
    except (InputError, RuntimeError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
