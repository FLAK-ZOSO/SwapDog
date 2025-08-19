# Swap watchdog

### Idea of functionality

The idea behind this gist is to provide a minimal daemon that...
- monitors the usage of RAM
- when the percentage exceeds a set treshold, selected swaps (swapfiles or swap partitions) are enabled
- when swaps are enabled and a 

It would be cool to be able to set from a configuration file different tresholds

### Rationale

It is meant to be useful when one doesn't want to swap memory if not strictly needed, but also doesn't want crashes.
- swap memory is always slower than RAM, especially HDDs are
- SSDs wears out with read and write cycles, while RAM doesn't

These reasons are enough for me to want to limit the usage of swap in a more radical way than [swappiness](https://askubuntu.com/a/157809/1559059) does.
