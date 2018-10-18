__version__ = "0.0.2a9"
__name__ = "aioupnp"
__author__ = "Jack Robison"
__maintainer__ = "Jack Robison"
__license__ = "MIT"
__email__ = "jackrobison@lbry.io"

import sys
import asyncio

if not hasattr(asyncio, "get_running_loop") and hasattr(asyncio, "_get_running_loop"):  # python 3.6
    setattr(sys.modules['asyncio'], "get_running_loop", asyncio._get_running_loop)
