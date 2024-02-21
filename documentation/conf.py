# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys
from unittest.mock import MagicMock
from sphinx.writers.html import HTMLTranslator
from docutils import nodes
from docutils.nodes import Element
sys.path.insert(0, os.path.abspath('../'))
# sys.path.insert(0, os.path.abspath('../bibdatamanagement'))

# -- Project information -----------------------------------------------------

project = 'BibData'
copyright = '2023, IPESE, EPFL'
author = 'J. Loustau'

# The full version, including alpha/beta/rc tags
release = '1.0'


# -- General configuration ---------------------------------------------------

extensions = ['sphinxcontrib.bibtex',
              'sphinx.ext.autodoc',
              'sphinx.ext.napoleon',
              'sphinx.ext.autosummary',
              'sphinx_design',
              'sphinx_copybutton',
              # 'sphinxcontrib.jquery',
              ]
# autosummary_generate = True  # Turn on sphinx.ext.autosummary
exclude_patterns = ['LICENSE']

# -- Bibliography ------------------------------------------------------------
bibtex_bibfiles = ['refs.bib']
bibtex_default_style = 'plain'
bibtex_reference_style = 'super'
bibtex_reference_sorting = None


# -- Options for HTML output -------------------------------------------------

html_theme = 'pydata_sphinx_theme'
html_sidebars = {
  "**": []
}

html_theme_options = {
  'gitlab_url': 'https://gitlab.epfl.ch/ipese/bibdatamanagement/bibdata-package/',
  'header_links_before_dropdown': 6,
  'navbar_align': 'left',
  "external_links": [{"name": "BibData_UI", "url": "https://gitlab.epfl.ch/ipese/bibdatamanagement/bibdatamanagement_ui"},],
  "icon_links": [{"name": "IPESE",
                  "url": "https://ipese-web.epfl.ch/ipese-blog/",
                  "icon": "https://github.com/IPESE/REHO/blob/documentation/documentation/images/logos/ipese_square.png?raw=true",
                  "type": "url"}],
  "logo": {"image_light": 'images/bibdata_logo.png',
           "image_dark": "images/bibdata_logo_black.png",
           "alt_text": "BibData documentation - Home"},
  "navigation_depth": 6
}
numfig = True  # Add figure numbering
numtab = True  # Add table numbering
add_function_parentheses = False
toc_object_entries_show_parents = 'all'

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css"
]

# html_js_files = [
#     '_static/js/custom.js'
# ]

# ------------ Autodoc ------------------------------------
autodoc_mock_imports = ['amplpy',
                        'pandas',
                        'openpyxl',
                        'numpy',
                        'scikit-learn',
                        'scikit-learn-extra',
                        'psycopg2',
                        'requests',
                        'sqlalchemy',
                        'scipy',
                        'matplotlib',
                        'plotly',
                        'geopandas',
                        'urllib3',
                        'dotenv']
sys.modules['scikit-learn'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['sklearn.metrics'] = MagicMock()
sys.modules['scikit-learn-extra'] = MagicMock()
sys.modules['sklearn_extra'] = MagicMock()
sys.modules['sklearn_extra.cluster'] = MagicMock()
sys.modules['sqlalchemy'] = MagicMock()
sys.modules['sqlalchemy.dialects'] = MagicMock()
sys.modules['shapely'] = MagicMock()


# ----------------- External links -------------------------------
class PatchedHTMLTranslator(HTMLTranslator):

    def visit_reference(self, node: Element) -> None:
        atts = {'class': 'reference'}
        if node.get('internal') or 'refuri' not in node:
            atts['class'] += ' internal'
        else:
            atts['class'] += ' external'
            # ---------------------------------------------------------
            # Customize behavior (open in new tab, secure linking site)
            atts['target'] = '_blank'
            atts['rel'] = 'noopener noreferrer'
            # ---------------------------------------------------------
        if 'refuri' in node:
            atts['href'] = node['refuri'] or '#'
            if self.settings.cloak_email_addresses and atts['href'].startswith('mailto:'):
                atts['href'] = self.cloak_mailto(atts['href'])
                self.in_mailto = True
        else:
            assert 'refid' in node, \
                'References must have "refuri" or "refid" attribute.'
            atts['href'] = '#' + node['refid']
        if not isinstance(node.parent, nodes.TextElement):
            assert len(node) == 1 and isinstance(node[0], nodes.image)
            atts['class'] += ' image-reference'
        if 'reftitle' in node:
            atts['title'] = node['reftitle']
        if 'target' in node:
            atts['target'] = node['target']
        self.body.append(self.starttag(node, 'a', '', **atts))

        if node.get('secnumber'):
            self.body.append(('%s' + self.secnumber_suffix) %
                             '.'.join(map(str, node['secnumber'])))


def setup(app):
    app.set_translator('html', PatchedHTMLTranslator)