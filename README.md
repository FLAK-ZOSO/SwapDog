# SwapDog

SwapDog is a *swap watchdog* that monitors RAM usage and enables swap devices only when necessary, based on user-defined thresholds. It is designed to prevent excessive swapping, which can lead to performance degradation, while still allowing the system to function without crashing when RAM is exhausted.

### Rationale

It is meant to be useful when one doesn't want to swap memory if not strictly needed, but also doesn't want crashes.

- swap memory is always slower than RAM, especially HDDs are
- SSDs wears out with read and write cycles, while RAM doesn't

These reasons are enough for me to want to limit the usage of swap in a more radical way than [swappiness](https://askubuntu.com/a/157809/1559059) does.

## Installation

Any installation method assumes that you have access to the `swapdog.py`, `swapdog.json`, `requirements.txt` and `swapdog.service` files in the current directory.

```bash
git clone https://github.com/FLAK-ZOSO/SwapDog
cd SwapDog
```

You may want to proceed with the [configuration](#configuration) before installing, but you can also do it later.

### Automated

You can use the provided [install.sh](install.sh) script to automate the installation process. Just run the following command:

```bash
chmod +x install.sh
./install.sh
```

### Manual

Take this as a documentation of the steps that the `install.sh` script performs, so you can do it manually if you prefer:

1. Install dependencies with `sudo pip3 install -r requirements.txt`
2. Copy the [swapdog.py](swapdog.py) file to `/usr/local/sbin/`
3. Make it executable with `sudo chmod 744 /usr/local/sbin/swapdog.py`
4. Copy the [swapdog.json](swapdog.json) file to `/etc/`
5. Copy the [swapdog.service](swapdog.service) file to `/etc/systemd/system/`
6. Enable the service with `sudo systemctl enable swapdog`
7. Start the service with `sudo systemctl start swapdog`
8. Check the status of the service with `sudo systemctl status swapdog`

## Configuration

In order to configure the behavior of SwapDog, you need to edit the `swapdog.json` file located in `/etc/`. The file follows a simple JSON structure that allows you to set thresholds and the swap devices to be used.

### Fields

- `thresholds`: An array of objects, each representing a threshold for enabling a swap device.
  - `percentage`: The percentage of RAM usage that triggers the swap device to be enabled.
  - `swap`: The path to the swap device (e.g., `/dev/sda1` or `/swapfile`).
- `period`: The time in seconds between checks of the RAM usage. Default is `1.0` seconds if not specified.

### How to configure

- Enable all swaps in order to make them easily detectable.

```bash
sudo swapon --all
```

- List the currently enabled swap devices.

```bash
sudo swapon --show
sudo cat /proc/swaps
```

What follows is an example output. You are looking for the `NAME` column to identify the swap devices.

```bash
NAME      TYPE      SIZE USED PRIO
/dev/dm-1 partition 7.4G   0B   -2
/swapfile file      2.0G   0B   -3
```

- Edit the `swapdog.json` file to set the desired thresholds and swap devices. For example, if you want to enable a swap device when RAM usage exceeds 95%, you can set it like this:

```json
{
    "thresholds": [
        {
            "percentage": 95.0,
            "swap": "/dev/dm-1"
        },
        {
            "percentage": 90.0,
            "swap": "/swapfile"
        }
    ],
    "period": 1.0
}
```
