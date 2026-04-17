"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify canonical TL;DR header enforcement for governed files under policy

- Later Extension Points:
    --> add more header fixtures only when covered language families or header rules expand

- Role:
    --> builds temporary files that model the governed header layout across languages
    --> checks missing markers template gaps and extra block-comment drift in isolated fixtures

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify.headers import check_headers
from tools.verify.policy import CODE_HEADER_TEMPLATE_FILE


def make_header_tree(repo_root: Path) -> None:
    (repo_root / 'docs' / 'templates').mkdir(parents=True)
    (repo_root / 'docs' / 'templates' / CODE_HEADER_TEMPLATE_FILE).write_text('ok\n')

    (repo_root / 'apps').mkdir(parents=True)
    (repo_root / 'tools').mkdir(parents=True)
    (repo_root / 'tools' / 'hooks').mkdir(parents=True)
    (repo_root / 'packages').mkdir(parents=True)
    (repo_root / '.github' / 'workflows').mkdir(parents=True)

    (repo_root / 'tools' / 'sample.py').write_text(
        '"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample python file\n\n'
        '- Later Extension Points:\n'
        '    --> add more checks later\n\n'
        '- Role:\n'
        '    --> keep sample verification behavior explicit\n\n'
        '- Exports:\n'
        '    --> `main()`\n\n'
        '- Consumed By:\n'
        '    --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """\n\n'
        'from __future__ import annotations\n'
    )
    (repo_root / 'apps' / 'sample.js').write_text(
        '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample js file\n\n'
        '- Later Extension Points:\n'
        '  --> add browser runtime seams later\n\n'
        '- Role:\n'
        '  --> keep sample app intent explicit\n\n'
        '- Exports:\n'
        '  --> `value`\n\n'
        '- Consumed By:\n'
        '  --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
        'const value = 1\n'
    )
    (repo_root / 'apps' / 'sample.css').write_text(
        '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample css file\n\n'
        '- Later Extension Points:\n'
        '  --> add more layout rules later\n\n'
        '- Role:\n'
        '  --> keep sample stylesheet intent explicit\n\n'
        '- Exports:\n'
        '  --> `sample` class rules\n\n'
        '- Consumed By:\n'
        '  --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
        '/* sample layout hook */\n'
        '.sample { display: block; }\n'
    )
    (repo_root / 'packages' / 'sample.ts').write_text(
        '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample ts file\n\n'
        '- Later Extension Points:\n'
        '  --> add typed runtime seams later\n\n'
        '- Role:\n'
        '  --> keep sample package intent explicit\n\n'
        '- Exports:\n'
        '  --> `value`\n\n'
        '- Consumed By:\n'
        '  --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
        'export const value = 1\n'
    )
    (repo_root / '.github' / 'workflows' / 'sample.yml').write_text(
        '#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        '# TL;DR  -->  sample workflow file\n'
        '#\n'
        '# - Later Extension Points:\n'
        '#   --> add more guarded workflow steps later\n'
        '#\n'
        '# - Role:\n'
        '#   --> keep sample workflow intent explicit\n'
        '#\n'
        '# - Exports:\n'
        '#   --> `sample` workflow\n'
        '#\n'
        '# - Consumed By:\n'
        '#   --> local verification tests\n'
        '# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'name: sample\n'
    )
    (repo_root / 'pyproject.toml').write_text(
        '#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        '# TL;DR  -->  sample python tooling configuration\n'
        '#\n'
        '# - Later Extension Points:\n'
        '#   --> add more repo-owned Python tooling settings later\n'
        '#\n'
        '# - Role:\n'
        '#   --> keep sample Python build and lint intent explicit\n'
        '#\n'
        '# - Exports:\n'
        '#   --> `build-system` and `tool.ruff` configuration\n'
        '#\n'
        '# - Consumed By:\n'
        '#   --> local verification tests\n'
        '# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        '[build-system]\n'
        'requires = ["setuptools>=61.0"]\n'
    )
    (repo_root / 'tools' / 'hooks' / 'pre-commit').write_text(
        '#!/usr/bin/env sh\n'
        '#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        '# TL;DR  -->  sample shell hook wrapper\n'
        '#\n'
        '# - Later Extension Points:\n'
        '#   --> add more governed shell hooks when repo controls expand\n'
        '#\n'
        '# - Role:\n'
        '#   --> keep sample hook intent explicit before commands run\n'
        '#\n'
        '# - Exports:\n'
        '#   --> `pre-commit` hook entrypoint\n'
        '#\n'
        '# - Consumed By:\n'
        '#   --> local verification tests\n'
        '# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'set -eu\n'
    )
    (repo_root / '.env.example').write_text(
        '#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        '# TL;DR  -->  sample environment contract\n'
        '#\n'
        '# - Later Extension Points:\n'
        '#   --> add more sample runtime variables when shared config grows\n'
        '#\n'
        '# - Role:\n'
        '#   --> keep sample environment ownership explicit for local tests\n'
        '#\n'
        '# - Exports:\n'
        '#   --> `PUBLIC_API_BASE_URL`\n'
        '#\n'
        '# - Consumed By:\n'
        '#   --> local verification tests\n'
        '# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'PUBLIC_API_BASE_URL=https://api.local.example\n'
    )


class TestVerifyHeaders(unittest.TestCase):
    def test_headers_pass_with_required_templates_and_markers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            issues = check_headers(repo_root)
            self.assertEqual(issues, [])

    def test_headers_fail_when_python_header_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'tools' / 'sample.py').write_text('from __future__ import annotations\n')
            issues = check_headers(repo_root)
            self.assertTrue(
                any('python file missing top-of-file TL;DR docstring' in issue for issue in issues)
            )

    def test_headers_fail_when_typescript_has_extra_block_comment(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'packages' / 'sample.ts').write_text(
                (repo_root / 'packages' / 'sample.ts').read_text() + '\n/* extra */\n'
            )
            issues = check_headers(repo_root)
            self.assertTrue(any('extra block comments' in issue for issue in issues))

    def test_headers_fail_when_code_template_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'docs' / 'templates' / CODE_HEADER_TEMPLATE_FILE).unlink()
            issues = check_headers(repo_root)
            self.assertTrue(
                any('missing required code header template' in issue for issue in issues)
            )

    def test_headers_fail_when_toml_header_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'pyproject.toml').write_text('[build-system]\n')
            issues = check_headers(repo_root)
            self.assertTrue(
                any(
                    'toml file missing top-of-file TL;DR comment block' in issue
                    for issue in issues
                )
            )

    def test_headers_fail_when_shell_header_is_missing_after_shebang(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'tools' / 'hooks' / 'pre-commit').write_text(
                '#!/usr/bin/env sh\nset -eu\n'
            )
            issues = check_headers(repo_root)
            self.assertTrue(
                any(
                    'shell file missing top-of-file TL;DR comment block' in issue
                    for issue in issues
                )
            )

    def test_headers_fail_when_shell_shebang_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'tools' / 'hooks' / 'pre-commit').write_text(
                '#  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
                '# TL;DR  -->  sample shell hook wrapper\n'
            )
            issues = check_headers(repo_root)
            self.assertTrue(
                any('shell file must begin with a shebang' in issue for issue in issues)
            )

    def test_headers_fail_when_dotenv_header_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / '.env.example').write_text('PUBLIC_API_BASE_URL=https://api.local.example\n')
            issues = check_headers(repo_root)
            self.assertTrue(
                any(
                    'dotenv file missing top-of-file TL;DR comment block' in issue
                    for issue in issues
                )
            )

    def test_headers_fail_when_css_header_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'apps' / 'sample.css').write_text('.sample { display: block; }\n')
            issues = check_headers(repo_root)
            self.assertTrue(
                any('css file missing top-of-file TL;DR block comment' in issue for issue in issues)
            )

    def test_headers_fail_when_javascript_header_is_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_header_tree(repo_root)
            (repo_root / 'apps' / 'sample.js').write_text('const value = 1\n')
            issues = check_headers(repo_root)
            self.assertTrue(
                any(
                    'javascript file missing top-of-file TL;DR block comment' in issue
                    for issue in issues
                )
            )


if __name__ == '__main__':
    unittest.main()
