"""Root conftest: make sure the project root is importable (for `import app`, `import db`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
