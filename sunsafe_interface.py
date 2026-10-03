"""
Backwards-compatible shim. The contract lives in `sunsafe/interface.py`; the model in
`sunsafe/model.py`.

`from sunsafe_interface import run_sunsafe, Inputs, Results` keeps working and runs the
real model.
"""

from sunsafe.interface import *  # noqa: F401,F403
from sunsafe.model import run_sunsafe  # noqa: F401
