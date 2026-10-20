# PLANTED DEFECT: trace_bag sleeps 4.5 seconds to simulate a slow legacy
# bag-tracing system. This stall is intentional and must not be fixed.
"""Baggage tool: trace a delayed, damaged or lost bag by file reference."""

import time
from copy import deepcopy

from acme.data import BAG_TRACES
from acme.errors import BagNotFound

LEGACY_STALL_SECONDS = 4.5


def trace_bag(file_reference: str) -> dict:
    time.sleep(LEGACY_STALL_SECONDS)
    trace = BAG_TRACES.get(file_reference.upper())
    if trace is None:
        raise BagNotFound(f"Bag file {file_reference} not found")
    return deepcopy(trace)
