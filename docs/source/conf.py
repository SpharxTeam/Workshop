# Copyright (c) 2026 SPHARX. All Rights Reserved. "From data intelligence emerges".
# docs/source/conf.py

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

project = 'workshop'
copyright = '2026, SPHARX'
author = 'SPHARX Team'
release = '1.0.3.6'

extensions = [
    'myst_parser',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'furo'
html_static_path = ['_static']

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "tasklist",
]

autodoc_typehints = "description"
autodoc_member_order = "bysource"