import sys

def check_version():
    import pandas as pd
    import exchange_calendars as xcal
    import numpy as np
    assert (sys.version.startswith("3.9.12 "))
    assert (pd.__version__ == "1.4.2")
    assert (xcal.__version__ == "3.6.3")
    assert (np.__version__ == "1.22.3")