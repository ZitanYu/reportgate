"""Allow ``python -m reportgate``."""

import sys

from .cli import main

sys.exit(main())
