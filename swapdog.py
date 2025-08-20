#!/usr/bin/python3
from __future__ import annotations
import os
import sys
import json
import time
import subprocess
import logging
import traceback

import psutil

__version__ = '0.1.0'
CONFIG_PATH = '/etc/swapdog.json'
PERIOD = 1.0
DISABLE_SWAPS = False
HYSTERESIS = 10


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
        "disable_swaps": DISABLE_SWAPS,
        "hysteresis": HYSTERESIS
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
    if "hysteresis" in parsed_config:
        configuration["hysteresis"] = parsed_config["hysteresis"]
    else:
        logging.warning(f"No hysteresis provided, defaulting to {HYSTERESIS}%.")
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
    logging.info(f"Enabling swap {swap}")
    try:
        subprocess.check_call(["swapon", swap])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error enabling swap {swap}: {e}")


def disable_swap(swap: str) -> None:
    """
    Disables the specified swap device.

    :param swap: Path to the swap device.
    :type swap: str
    """
    logging.info(f"Disabling swap {swap}")
    try:
        subprocess.check_call(["swapoff", swap])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error disabling swap {swap}: {e}")


def get_swap_usage_map() -> dict[str, tuple[int, int]]:
    """
    Returns a mapping of swap device paths to (used, total) in bytes.

    :return: Mapping between swaps and their used and total memory
    :rtype: dict[str, tuple[int, int]]
    """
    usage_map = {}
    try:
        output = subprocess.check_output([
            "swapon", "--show=NAME,USED,SIZE", "--noheadings", "--raw", "--bytes"
        ]).decode("utf-8")
        for line in output.splitlines():
            logging.debug(line)
            parts = line.split()
            if len(parts) >= 3:
                path = parts[0]
                used = int(parts[1])
                total = int(parts[2])
                usage_map[path] = (used, total)
    except subprocess.CalledProcessError as e:
        logging.warning(f"Error running swapon command: {e}")
    except UnicodeDecodeError as e:
        logging.warning(f"Error decoding swapon output: {e}")
    except ValueError as e:
        logging.warning(f"Error parsing swapon output: {e}")
    return usage_map


def should_disable_swap(threshold: Threshold, usage_map: dict[str, tuple[int, int]], vmem_info: tuple[int, int], hysteresis: float) -> bool:
    """
    Decide if swap should be disabled based on RAM+swap free and a threshold.

    :param threshold: The threshold we want to untrigger
    :type threshold: Threshold
    :param usage_map: Mapping between swaps and their (used, total) memory in bytes
    :type usage_map: dict[str, tuple[int, int]]
    :param vmem_info: Information on (not_free, total) bytes of the virtual memory usage
    :type vmem_info: tuple[int, int]
    :param hysteresis: Percentage margin under the threshold for it to be untriggered
    :type hysteresis: float
    :return: Whether to disable the swap or not
    :rtype: bool
    """
    logging.debug(usage_map)
    if threshold.swap not in usage_map:
        logging.warning(f"Swap {threshold.swap} not found in usage_map; cannot determine if it should be disabled.")
        return False
    swap_info = usage_map[threshold.swap]
    swap_used = swap_info[0]
    ram_not_free = vmem_info[0]
    ram_total = vmem_info[1]
    logging.debug(f"{ram_total=} {ram_not_free=} {swap_used=}")
    memory_over_ram = (ram_not_free + swap_used)/ram_total
    logging.debug(f"Using {100*memory_over_ram:.2f}% of the RAM")
    if 100*memory_over_ram + hysteresis < threshold.percentage:
        return True
    return False


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
            vmem_info = psutil.virtual_memory()
            logging.debug(f"Current virtual memory: {vmem_info.percent}%")
            swap_usage = get_swap_usage_map()
            enabled_swaps = set(swap_usage.keys())
            for t in thresholds:
                logging.debug(f"Checking {t}")
                logging.debug(f"{vmem_info.total=} {vmem_info.used=}")
                if vmem_info.percent >= t.percentage:
                    logging.debug(f"Memory above {t.percentage}% threshold")
                    if t.swap in enabled_swaps:
                        logging.debug(f"Swap {t.swap} already enabled")
                        continue
                    logging.info(f"{t} exceeded")
                    enable_swap(t.swap)
                elif configuration["disable_swaps"] and t.swap in enabled_swaps \
                    and should_disable_swap(
                        t, swap_usage,
                        (vmem_info.total - vmem_info.free, vmem_info.total),
                        hysteresis=configuration["hysteresis"]
                    ):
                    # https://stackoverflow.com/questions/2580136/does-python-support-short-circuiting
                    logging.info(f"{t} untriggered")
                    disable_swap(t.swap)
                    enabled_swaps.remove(t.swap)
            time.sleep(configuration["period"])
    except Exception as e:
        logging.error(f"Fatal error in main loop. {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)
