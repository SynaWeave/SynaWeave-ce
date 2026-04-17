"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TL;DR  -->  verify deterministic comment-heavy note-taking checks across governed syntax families

- Later Extension Points:
    --> add more family fixtures only when governed comment-bearing surfaces expand

- Role:
    --> builds temporary files that model local comment density and commented-out code failures
    --> keeps comment-heavy repo controls mechanical without relying on hook-only review habits

- Exports:
    --> unit test cases only

- Consumed By:
    --> Python unit test discovery during repository verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.verify.commentary import check_commentary


def make_commentary_tree(repo_root: Path) -> None:
    (repo_root / 'apps').mkdir(parents=True)
    (repo_root / 'packages').mkdir(parents=True)
    (repo_root / 'tools').mkdir(parents=True)
    (repo_root / '.github' / 'workflows').mkdir(parents=True)

    (repo_root / 'tools' / 'sample.py').write_text(
        '"""  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample python file\n\n'
        '- Later Extension Points:\n'
        '    --> add more logic later\n\n'
        '- Role:\n'
        '    --> keep sample intent explicit\n\n'
        '- Exports:\n'
        '    --> `sample()`\n\n'
        '- Consumed By:\n'
        '    --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  """\n\n'
        '# keep the sample callable visible for commentary coverage\n'
        'def sample():\n'
        '    return 1\n'
    )
    (repo_root / 'packages' / 'sample.ts').write_text(
        '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample ts file\n\n'
        '- Later Extension Points:\n'
        '  --> add more typed helpers later\n\n'
        '- Role:\n'
        '  --> keep sample package intent explicit\n\n'
        '- Exports:\n'
        '  --> `value`\n\n'
        '- Consumed By:\n'
        '  --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
        '// keep a local why note near the exported value\n'
        'export const value = 1;\n'
    )
    (repo_root / 'apps' / 'sample.css').write_text(
        '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
        'TL;DR  -->  sample css file\n\n'
        '- Later Extension Points:\n'
        '  --> add more style hooks later\n\n'
        '- Role:\n'
        '  --> keep sample style intent explicit\n\n'
        '- Exports:\n'
        '  --> `.sample` rules\n\n'
        '- Consumed By:\n'
        '  --> local verification tests\n'
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
        '/* keep the selector role obvious */\n'
        '.sample { display: block; }\n'
    )
    (repo_root / 'apps' / 'sample.html').write_text(
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<body>\n'
        '  <!-- keep the placeholder page purpose explicit -->\n'
        '  <main>sample</main>\n'
        '</body>\n'
        '</html>\n'
    )


class TestVerifyCommentary(unittest.TestCase):
    def test_commentary_passes_when_local_notes_exist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_commentary_tree(repo_root)
            self.assertEqual(check_commentary(repo_root), [])

    def test_commentary_rejects_commented_out_code(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_commentary_tree(repo_root)
            (repo_root / 'apps' / 'sample.html').write_text(
                '<!DOCTYPE html>\n<!-- <div>old</div> -->\n<html></html>\n'
            )
            issues = check_commentary(repo_root)
            self.assertTrue(any('commented-out code is banned' in issue for issue in issues))

    def test_commentary_rejects_multiline_css_comments(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            repo_root = Path(raw_tmp)
            make_commentary_tree(repo_root)
            (repo_root / 'apps' / 'sample.css').write_text(
                '/*  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n'
                'TL;DR  -->  sample css file\n\n'
                '- Later Extension Points:\n'
                '  --> add more style hooks later\n\n'
                '- Role:\n'
                '  --> keep sample style intent explicit\n\n'
                '- Exports:\n'
                '  --> `.sample` rules\n\n'
                '- Consumed By:\n'
                '  --> local verification tests\n'
                '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  */\n\n'
                '/* one intent\nsecond intent */\n'
                '.sample { display: block; }\n'
            )
            issues = check_commentary(repo_root)
            self.assertTrue(
                any('css comments must stay one physical line' in issue for issue in issues)
            )
