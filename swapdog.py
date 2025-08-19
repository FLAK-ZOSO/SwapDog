#!/usr/bin/python3
from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import logging

import psutil


CONFIG = '/etc/swapdog.json'
PERIOD = 1.0


class Threshold:

    def __init__(self, percentage: float, swap: str):
        self.percentage = percentage
        self.swap = os.path.realpath(swap)
    
    def __repr__(self):
        return f"<Threshold at {self.percentage}% for {self.swap}>"


def read_configuration(path: str) -> tuple[list[Threshold], float]:
    try:
        with open(path, "r") as config_file:
            config = json.load(config_file)
    except IOError as io_error:
        logging.error(f"Error: could not open {path}")
        sys.exit(72)
    except json.JSONDecodeError as json_error:
        logging.error(f"Error: invalid JSON in {path}")
        sys.exit(78)
    thresholds: list[Threshold] = []
    for t in config["thresholds"]:
        thresholds.append(Threshold(t["percentage"], t["swap"]))
    if "period" in config:
        return (thresholds, config["period"])
    logging.warning(f"No period provided, defaulting to {PERIOD} seconds")
    return (thresholds, PERIOD)


def list_enabled_swaps() -> list[bytes]:
    return subprocess.check_output([
        "swapon", "--show=NAME", "--raw", "--noheadings"
    ]).splitlines()


def enable_swap(swap: str) -> None:
    logging.info(f"Attempt to enable {swap}")
    try:
        subprocess.check_call(["swapon", swap])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error enabling swap {swap}: {e}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s SwapDog[%(process)d] %(levelname)s %(message)s"
    )
    if len(sys.argv) > 1:
        thresholds, period = read_configuration(sys.argv[1])
    else:
        logging.warning(f"No configuration path provided, defaulting to {CONFIG}")
        thresholds, period = read_configuration(CONFIG)
    logging.info(f"Starting with {thresholds}")
    while True:
        current = psutil.virtual_memory().percent
        logging.debug(f"Current virtual memory: {current}%")
        enabled_swaps = map(lambda x: x.decode('utf-8'), list_enabled_swaps())
        for t in thresholds:
            logging.debug(f"Checking {t}")
            if current >= t.percentage:
                if t.swap in enabled_swaps:
                    continue
                logging.info(f"{t} exceeded")
                enable_swap(t.swap)
        time.sleep(period)
