"""The inspect-evals-readmes command."""

import argparse
import sys
from pathlib import Path

from inspect_evals_utils.readmes.generate import TaskImportError, generate_readmes
from inspect_evals_utils.readmes.sections import add_section


def main(argv: list[str] | None = None) -> int:
    """Run the command. Returns the exit status."""
    parser = argparse.ArgumentParser(
        prog="inspect-evals-readmes",
        description="Generate and maintain auto-generated README sections for Inspect evals",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate", help="rewrite the generated sections")
    gen.add_argument(
        "--src", default="src", help="directory holding <eval>/eval.yaml (default: src)"
    )
    gen.add_argument("--eval", default=None, help="only this eval (package name, e.g. my_eval)")
    gen.add_argument(
        "--create-missing", action="store_true", help="create READMEs that don't exist"
    )
    gen.add_argument("--include-examples", action="store_true", help="also process examples/")
    gen.add_argument(
        "--check", action="store_true", help="exit 1 if any README would change; write nothing"
    )

    add = subparsers.add_parser("add-section", help="add missing section tags to READMEs")
    add.add_argument(
        "--src", default="src", help="directory holding <eval>/eval.yaml (default: src)"
    )
    add.add_argument("--key", required=True, help='section key, e.g. "Parameters"')
    add.add_argument(
        "--insert-after",
        action="append",
        default=[],
        help="section key to insert after; repeatable, in priority order",
    )

    args = parser.parse_args(argv)
    if args.command == "generate":
        try:
            changed = generate_readmes(
                Path(args.src),
                eval_name=args.eval,
                create_missing=args.create_missing,
                include_examples=args.include_examples,
                check=args.check,
            )
        except (LookupError, TaskImportError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        if args.check and changed:
            print("READMEs out of date:", *(str(p) for p in changed), sep="\n  ")
            return 1
        return 0
    add_section(Path(args.src), args.key, args.insert_after)
    return 0


if __name__ == "__main__":
    sys.exit(main())
