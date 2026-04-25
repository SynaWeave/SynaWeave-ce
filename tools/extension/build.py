"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  build stripped extension HTML so source notes stay local and shipped files stay bare

- Later Extension Points:
    --> add broader extension packaging steps only when the repo grows a real release artifact path

- Role:
    --> copies the extension source tree into a build artifact directory
    --> strips HTML comments from shipped files while source comments stay local in development

- Exports:
    --> `build_extension()`
    --> `main()`

- Consumed By:
    --> local operators CI and HTML ship verification checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from tools.dev.typescript import run_tsc

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_html_comments(text: str) -> str:
    # Strip HTML comments from shipped artifacts
    # Source-only notes must never leak into client surfaces
    return HTML_COMMENT_RE.sub("", text)


def _compile_typescript_sources(source_dir: Path, output_dir: Path) -> None:
    # Emit JavaScript runtime artifacts for extension entrypoints
    # while source stays TypeScript-first
    ts_paths = sorted(source_dir.glob("*.ts"))
    if not ts_paths:
        return

    tsconfig_path = source_dir / "tsconfig.json"
    if not tsconfig_path.exists():
        raise FileNotFoundError(
            f"missing extension TypeScript build config: {tsconfig_path}"
        )

    repo_root = Path(__file__).resolve().parents[2]
    run_tsc(
        repo_root=repo_root,
        tsconfig_path=tsconfig_path,
        output_dir=output_dir,
        root_dir=source_dir,
    )


def build_extension(source_dir: Path, output_dir: Path) -> None:
    # Rebuild from scratch so old packaged files never survive after source changes
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(
        source_dir,
        output_dir,
        ignore=shutil.ignore_patterns("*.ts", "*.d.ts", "tsconfig.json"),
    )

    _compile_typescript_sources(source_dir, output_dir)

    # Rewrite only HTML files so JS CSS and manifest assets preserve their source formatting
    for html_path in sorted(output_dir.glob("*.html")):
        html_path.write_text(strip_html_comments(html_path.read_text()))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build stripped extension artifacts")
    parser.add_argument(
        "--source",
        default="apps/extension",
        help="Extension source directory",
    )
    parser.add_argument(
        "--output",
        default="build/extension",
        help="Extension artifact directory",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    build_extension(Path(args.source), Path(args.output))
    print(f"Built stripped extension artifact at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
