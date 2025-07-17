import os
import sys
sys.path.insert(0, os.path.abspath('.'))

project = 'wicdpico'
copyright = '2025, Joe Pardue'
author = 'Joe Pardue'
release = '1.0'

extensions = [
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'code.py', 'boot.py']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
