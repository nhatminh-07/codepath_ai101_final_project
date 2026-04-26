"""CLI entrypoint for the RepoFinder RAG + agentic workflow."""

from __future__ import annotations

import argparse
import json
import logging

try:
    from .repofinder import RepoFinderSystem, configure_logging
except ImportError:
    from repofinder import RepoFinderSystem, configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run RepoFinder on local documents")
    parser.add_argument("query", help="Question or planning prompt")
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more .md/.txt/.csv files to index for retrieval",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Retriever top-k")
    parser.add_argument(
        "--feedback",
        default="",
        help="Optional human feedback note stored in memory for this run",
    )
    return parser


def main() -> None:
    configure_logging(logging.INFO)
    parser = build_parser()
    args = parser.parse_args()

    system = RepoFinderSystem(top_k=args.top_k)
    output = system.run(query=args.query, file_paths=args.paths)

    if args.feedback:
        system.submit_human_feedback(args.feedback)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
