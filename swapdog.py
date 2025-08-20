#!/usr/bin/python3
from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import logging
from collections import namedtuple

import psutil

__version__ = '0.1.0'
CONFIG_PATH = '/etc/swapdog.json'
PERIOD = 1.0
DISABLE_SWAPS = False


class Threshold:
    """
    Represents a memory usage threshold and associated swap device.

    :param percentage: Memory usage percentage to trigger swap.
    :type percentage: float
    :param swap: Path to the swap device.
    :type swap: str
    """

    def __init__(self, percentage: float, swap: str):
        self.percentage = percentage
        self.swap = os.path.realpath(swap)
    
    def __repr__(self):
        """
        Returns a string representation of the Threshold.

        :return: String representation.
        :rtype: str
        """
        return f"<Threshold at {self.percentage}% for {self.swap}>"


def read_configuration(path: str) -> tuple[list[Threshold], dict[str, float | bool]]:
    """
    Reads and parses the configuration file.

    :param path: Path to the configuration file.
    :type path: str
    :return: List of Threshold objects and the configuration parameters.
    :rtype: tuple[list[Threshold], dict[float, bool]]
    :raises SystemExit: If the file cannot be opened (exit code 72) or JSON is malformed (exit code 78).
    """
    try:
        with open(path, "r") as config_file:
            parsed_config = json.load(config_file)
    except IOError:
        logging.error(f"Error: could not open {path}")
        sys.exit(72)
    except json.JSONDecodeError:
        logging.error(f"Error: invalid JSON in {path}")
        sys.exit(78)
    thresholds: list[Threshold] = []
    for t in parsed_config["thresholds"]:
        thresholds.append(Threshold(t["percentage"], t["swap"]))
    configuration: dict[str, float | bool] = {
        "period": PERIOD,
        "disable_swaps": DISABLE_SWAPS
    }
    if "period" in parsed_config:
        configuration["period"] = parsed_config["period"]
    else:
        logging.warning(f"No period provided, defaulting to {PERIOD} seconds")
    if "disable_swaps" in parsed_config:
        configuration["disable_swaps"] = parsed_config["disable_swaps"]
    else:
        logging.warning(
            f"No disable_swaps provided, defaulting to {DISABLE_SWAPS}. Swaps will "
            f"{'not ' if not DISABLE_SWAPS else ''}be automatically disabled"
        )
    return (thresholds, configuration)


def list_enabled_swaps() -> list[bytes]:
    """
    Lists currently enabled swap devices.

    :return: List of swap device paths as bytes.
    :rtype: list[bytes]
    """
    return subprocess.check_output([
        "swapon", "--show=NAME", "--raw", "--noheadings"
    ]).splitlines()


def enable_swap(swap: str) -> None:
    """
    Enables the specified swap device.

    :param swap: Path to the swap device.
    :type swap: str
    """
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
        thresholds, configuration = read_configuration(sys.argv[1])
    else:
        logging.warning(f"No configuration path provided, defaulting to {CONFIG_PATH}")
        thresholds, configuration = read_configuration(CONFIG_PATH)
    logging.info(f"Starting with {thresholds}")
    try:
        while True:
            current = psutil.virtual_memory().percent
            logging.debug(f"Current virtual memory: {current}%")
            enabled_swaps = set(x.decode('utf-8') for x in list_enabled_swaps())
            for t in thresholds:
                logging.debug(f"Checking {t}")
                if current >= t.percentage:
                    if t.swap in enabled_swaps:
                        continue
                    logging.info(f"{t} exceeded")
                    enable_swap(t.swap)
            time.sleep(configuration["period"])
    except Exception as e:
        logging.error(f"Fatal error in main loop. {e}")
        sys.exit(1)
