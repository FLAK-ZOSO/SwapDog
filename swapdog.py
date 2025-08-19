#!/usr/bin/python3
from __future__ import annotations
import os
import sys
import json
import time
import subprocess

import psutil


CONFIG = '/etc/swapdog.json'
PERIOD = 1


class Threshold:
    percentage: float
    swap: str
    enabled: bool

    def __init__(self, percentage: float, swap: str):
        object.__setattr__(self, "percentage", percentage)
        object.__setattr__(self, "swap", os.path.realpath(swap))
    
    def __repr__(self):
        return f"<Treshold at {self.percentage}% for {self.swap}>"


def read_configuration(path: str) -> tuple[list[Threshold], float]:
    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
    except IOError as io_error:
        print(f"Error: could not open {path}", file=sys.stderr)
        raise io_error
    thresholds: list[Threshold] = []
    for t in config["thresholds"]:
        thresholds.append(Threshold(t["percentage"], t["swap"]))
    if "period" in config:
        return (thresholds, config["period"])
    return (thresholds, PERIOD)

def list_enabled_swaps() -> list[bytes]:
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
        print(current, file=sys.stderr)
        enabled_swaps = map(lambda x: x.decode('utf-8'), list_enabled_swaps())
        print(enabled_swaps, file=sys.stderr)
        for t in thresholds:
            print(t, file=sys.stderr)
            if current >= t.percentage:
                if t.swap in enabled_swaps:
                    continue
                enable_swap(t.swap)
        time.sleep(period)
