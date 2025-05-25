"""Configuration for pytest."""

import os
import sys

# Añadir el directorio raíz del proyecto al PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
