#!/usr/bin/python3
import sys
import json
import time
import psutil
import subprocess
from typing import NamedTuple


CONFIG = '/etc/swapdog.json'
PERIOD = 1


class Threshold(NamedTuple):
    percentage: float
    swap: str
    enabled: bool


def read_configuration(path: str) -> tuple[list[Threshold], float]:
    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
    except IOError as io_error:
        print(f"Error: could not open {path}", file=sys.stderr)
        raise io_error
    thresholds: list[Threshold] = []
    for t in config["thresholds"]:
        thresholds.append(Threshold(t["percentage"], t["swap"], False))
    if "period" in config:
        return (thresholds, config["period"])
    return (thresholds, PERIOD)

def list_enabled_swaps() -> list[str]:
    return subprocess.check_output([
        "swapon", "--show=NAME", "--raw", "--noheadings"
    ]).splitlines()

def enable_swap(swap: str) -> None:
    subprocess.check_call(["swapon", swap])

if __name__ == '__main__':
    thresholds, period = read_configuration(sys.argv[1] if len(sys.argv) > 1 else CONFIG)
    print(thresholds, file=sys.stderr)
    while True:
        current = psutil.virtual_memory().percent
        enabled_swaps = list_enabled_swaps()
        for t in thresholds:
            if t.enabled:
                continue
            if t.percentage >= current:
                if t.swap in enabled_swaps:
                    t.enabled = True
                    continue
                enable_swap(t.swap)
        time.sleep(period)
