"""
Backwards-compatible shim. The contract now lives in `sunsafe/interface.py`.

`from sunsafe_interface import run_sunsafe, Inputs, Results` keeps working.
"""

from sunsafe.interface import *  # noqa: F401,F403
from sunsafe.interface import run_sunsafe, run_sunsafe_fake  # noqa: F401  (explicit for IDEs)
