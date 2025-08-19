#!/usr/bin/python3
import sys
import json
from typing import NamedTuple

CONFIG = '/etc/swapdog.json'


class Threshold(NamedTuple):
    percentage: float
    swap: str


def read_configuration(path: str) -> list[Threshold]:
    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
    except IOError as io_error:
        print(f"Error: could not open {path}", file=sys.stderr)
        raise io_error
    thresholds: list[Threshold] = []
    for t in config["thresholds"]:
        thresholds.append(Threshold(t["percentage"], t["swap"]))
    return thresholds

if __name__ == '__main__':
    thresholds = read_configuration(sys.argv[1] if len(sys.argv) > 1 else CONFIG)
    print(thresholds, file=sys.stderr)
