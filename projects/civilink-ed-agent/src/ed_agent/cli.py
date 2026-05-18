"""CLI entrypoint: `python -m ed_agent <command>`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ed_agent import __version__, issue_logger
from ed_agent.config import ISSUES_OPEN_DIR, PROJECT_ROOT


def _cmd_hello(_args: argparse.Namespace) -> int:
    print(f"civilink-ed-agent v{__version__}")
    print(f"project root: {PROJECT_ROOT}")
    print(f"issues (open): {ISSUES_OPEN_DIR}")
    return 0


def _cmd_issues_new(args: argparse.Namespace) -> int:
    issue_path = issue_logger.create_issue(
        track=args.track,
        severity=args.severity,
        category=args.category,
        source=args.source,
        project=args.project,
        phenomenon=args.phenomenon or "(TODO)",
        decision=args.decision or "(TODO)",
        reason_for_human=args.reason or "(TODO)",
        hypothesis=args.hypothesis or "(TODO)",
        file=args.file,
    )
    print(f"created: {issue_path}")
    return 0


def _cmd_issues_report(_args: argparse.Namespace) -> int:
    summary = issue_logger.summarize_open()
    print(summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ed_agent", description="civilink-ed-agent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # hello
    p_hello = sub.add_parser("hello", help="smoke test: print project info")
    p_hello.set_defaults(func=_cmd_hello)

    # issues new
    p_iss = sub.add_parser("issues", help="manage issue log")
    iss_sub = p_iss.add_subparsers(dest="issues_cmd", required=True)

    p_iss_new = iss_sub.add_parser("new", help="create a new issue MD")
    p_iss_new.add_argument("--track", choices=["A", "B"], default="B")
    p_iss_new.add_argument(
        "--severity",
        choices=["blocker", "major", "minor", "question"],
        default="minor",
    )
    p_iss_new.add_argument("--category", required=True)
    p_iss_new.add_argument("--source", required=True)
    p_iss_new.add_argument("--project", default="")
    p_iss_new.add_argument("--file", default="")
    p_iss_new.add_argument("--phenomenon", default="")
    p_iss_new.add_argument("--decision", default="")
    p_iss_new.add_argument("--reason", default="")
    p_iss_new.add_argument("--hypothesis", default="")
    p_iss_new.set_defaults(func=_cmd_issues_new)

    p_iss_rep = iss_sub.add_parser("report", help="summarize open issues")
    p_iss_rep.set_defaults(func=_cmd_issues_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
