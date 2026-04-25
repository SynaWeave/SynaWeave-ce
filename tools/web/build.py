"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  build the static web artifact so source files stay authoritative
and served files stay generated

- Later Extension Points:
    --> add broader browser asset assembly only when the web shell grows
        beyond plain static files plus TypeScript

- Role:
    --> copies the web source shell into a generated build artifact directory
    --> compiles TypeScript browser entrypoints into browser-ready JavaScript in that build output

- Exports:
    --> `build_web()`
    --> `main()`

- Consumed By:
    --> local dev browser verification and any plain static serving of the web shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from tools.dev.typescript import run_tsc


def _compile_typescript_sources(source_dir: Path, output_dir: Path) -> None:
    ts_paths = sorted(source_dir.glob("*.ts"))
    if not ts_paths:
        return

    tsconfig_path = source_dir / "tsconfig.build.json"
    if not tsconfig_path.exists():
        raise FileNotFoundError(
            f"missing web TypeScript build config: {tsconfig_path}"
        )

    repo_root = Path(__file__).resolve().parents[2]
    run_tsc(
        repo_root=repo_root,
        tsconfig_path=tsconfig_path,
        output_dir=output_dir,
        root_dir=source_dir,
    )


def build_web(source_dir: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(
        source_dir,
        output_dir,
        ignore=shutil.ignore_patterns("*.ts", "*.d.ts", "tsconfig*.json"),
    )

    _compile_typescript_sources(source_dir, output_dir)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static web artifacts")
    parser.add_argument("--source", default="apps/web", help="Web source directory")
    parser.add_argument("--output", default="build/web", help="Web artifact directory")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    build_web(Path(args.source), Path(args.output))
    print(f"Built web artifact at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
