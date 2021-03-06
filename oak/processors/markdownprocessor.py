# -*- coding: utf-8 -*-
"""
    The Pygments Markdown Preprocessor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This fragment is a Markdown_ preprocessor that renders source code
    to HTML via Pygments.  To use it, invoke Markdown like so::

        from markdown import Markdown

        md = Markdown()
        md.preprocessors.insert(0, CodeBlockPreprocessor())
        markdown = md.__str__

    markdown is then a callable that can be passed to the context of
    a template and used in that template, for example.

    This uses CSS classes by default, so use
    ``pygmentize -S <some style> -f html > pygments.css``
    to create a stylesheet to be added to the website.

    You can then highlight source code in your markdown markup::

        [sourcecode:lexer]
        some code
        [/sourcecode]

    .. _Markdown: http://www.freewisdom.org/projects/python-markdown/

    :copyright: 2007 by Jochen Kupperschmidt.
    :license: BSD, see LICENSE for more details.
"""

# Options
# ~~~~~~~

# Set to True if you want inline CSS styles instead of classes
INLINESTYLES = True


import re

from markdown.preprocessors import Preprocessor

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, TextLexer


class CodeBlockPreprocessor(Preprocessor):

    pattern = re.compile(
        r'\[sourcecode:(.+?)\](.+?)\[/sourcecode\]', re.S)


    def run(self, lines):
        def repl(m):
            try:
                lexer = get_lexer_by_name(m.group(1))
            except ValueError:
                lexer = TextLexer()
            formatter = HtmlFormatter(noclasses=INLINESTYLES)
            code = highlight(m.group(2), lexer, formatter)
            code = code.replace('\n\n', '\n&nbsp;\n')
            return '\n\n<div class="code">%s</div>\n\n' % code
        return self.pattern.sub(
            repl, '\n'.join(lines)).split('\n')
