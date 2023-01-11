# xkcdlock-py
A reimagination of the [xkcdlock](https://github.com/bbusse/xkcdlock) in Python.

This is a wrapper around a locking program (swaylock or i3lock) to display an XKCD comic on the lock screen.
Depending on the mode of choice, the program will download and display the latest, a random or a specific XKCD comic.
The program uses a specified directory to cache images and will fallback to an already downloaded image when no internet connection can be established.

## Features

* Displays the XKCD comic, title and caption on the lock screen as background
* 3 modes of operation: latest, random, and index (one specific comic)
* Download cooldown setting and image caching to prevent the system from making too many HTTP requests
* Fallback and offline mode

## Installation

### Python dependencies
The following python dependencies are required (available through your favorite python package manager):
`urllib`, `wand`

For ArchLinux, you can install them as `extra/python-urllib3` and `community/python-wand`.

### Other dependencies
You will also need Imagick for the image processing to work.

Installation for Ubuntu/Debian:
```
apt-get install libmagickwand-dev
```

Installation for ArchLinux:
```
pacman -S extra/imagemagick
```

`xrandr` is required to query the screen resolution.

### Installation

After installing the dependencies, the program `xkcdlock.py` is ready to use.

Enable the executable flag on `xkcdlock.py` and place it in a PATH-directory (e.g., your local bin folder), if you want to call it directly from the command line.

## Usage

See `xkcdlock.py --help` for all available options.

Use
```
xkcdlock.py [options] MODE
```
You must provide a mode for xkcdlock to work.
The mode determines the strategy by which xkcdlock-py downloads and displays.
The modes are:

* `latest`: The program will download and display the latest comic of the day
* `random`: The program will choose a random comic to download
* `index`: The program will download the comic with the number given by the option `-i INDEX`

Further options you may want to specify are:

* `-d DIR`: Give a directory which should be used to cache data and export the generated background images. If this is not given, the program will use `/tmp/xkcdlock` as default.
* `-l LOCK`: Specify the locking program (by default `swaylock`). Any locking binary can be given, it should support the calling conventions of i3lock, with the options `-u`, `-s`, and `-i`. Currently, only swaylock and i3lock are supported.
* `-c COOLDOWN`: If a cooldown in the format `HH:MM` is given, the program will not attempt any new HTTP-requests to the XKCD website until the cooldown period has elapsed after the latest download. Instead, the cached data will exclusively be used to display an image. The cooldown will be ignored, if no cached data is available.
* `-f MODE`: Select a mode which will be used when no internet connection can be established. For example, you may want to display the latest image when the internet connection is available, but display a random image when there is no internet connection. To achieve this, use mode `latest` as positional argument and fallback mod `-f random` as an option.
* `-i INDEX`: The index for index mode.
* `-o`: Enable offline mode, no connections to the internet will be made.
* `-v`: Enable verbose logging.

## Disclaimer

This program has been written in a way, that it should always call the locking binary, even if internal errors occur.
However, there is no guarantee that this will always happen.
You are responsible for the security of your system, use this script at your own risk.
Securely locking your computer is important for the security of your computer in unsafe environments, therefore you should refrain from using this program in automated scripts (suck as locking timers) and on safety-critical systems.
Be aware of potential side-channel attacks through the internet connection attempts.
The locking script should not be publicly accessible by other users on a shared system.

If you wish to use the XKCD comic in automated locking scripts, consider using the generated background image (located in `DIR/lock.png`) in your scripted call as background source.

## Contribution

Fell free to open issues on bugs / problems / feature requests.

## Acknowledgements

Björn Busse for writing the original xkcdlock: https://github.com/bbusse/xkcdlock
