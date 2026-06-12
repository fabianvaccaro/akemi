"""CLI interface for Akemi - argparse subcommands dispatching to modules."""
import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="akemi",
        description="AI-friendly graph-based codebase documentation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # bootstrap
    p_boot = sub.add_parser("bootstrap", help="Scan codebase and generate graph nodes")
    p_boot.add_argument("project_root", nargs="?", default=".", help="Project root (default: .)")
    p_boot.add_argument("depth", nargs="?", default="tier2", choices=["tier1", "tier2"],
                        help="Scan depth: tier1=modules only, tier2=modules+files+classes+tests")

    # rebuild-index
    p_idx = sub.add_parser("rebuild-index", help="Rebuild graph index from node files")
    p_idx.add_argument("akemi_dir", nargs="?", default=".akemi", help="Akemi directory (default: .akemi)")

    # rebuild-views
    p_views = sub.add_parser("rebuild-views", help="Generate markdown view files")
    p_views.add_argument("akemi_dir", nargs="?", default=".akemi", help="Akemi directory (default: .akemi)")

    # validate
    p_val = sub.add_parser("validate", help="Validate graph integrity")
    p_val.add_argument("akemi_dir", nargs="?", default=".akemi", help="Akemi directory (default: .akemi)")

    # sync-claude
    p_sync = sub.add_parser("sync-claude", help="Sync Claude agent files into .claude/")
    p_sync.add_argument("project_root", nargs="?", default=".", help="Project root (default: .)")

    args = parser.parse_args(argv)

    if args.command == "bootstrap":
        from .bootstrap import run_bootstrap
        run_bootstrap(args.project_root, args.depth)

    elif args.command == "rebuild-index":
        from .index_builder import build_index
        msg = build_index(args.akemi_dir)
        print(msg)

    elif args.command == "rebuild-views":
        from .view_generator import rebuild_views
        msg = rebuild_views(args.akemi_dir)
        print(msg)

    elif args.command == "validate":
        from .validator import validate
        result = validate(args.akemi_dir)
        print(result.report())
        sys.exit(result.error_count)

    elif args.command == "sync-claude":
        from .sync_claude import sync_claude
        try:
            print(sync_claude(args.project_root))
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)
