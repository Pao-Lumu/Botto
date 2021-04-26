from pip._internal import main as pipmain

_all_ = [
    "toml",
    "aiofiles >= 0.4.0",
    "colorama >= 0.4.1",
    "discord.py[voice] >= 1.3.2",
    "mcrcon >= 0.5.2",
    "mcstatus >= 2.2.1",
    "pyfiglet >= 0.8.post1",
    "python-valve >= 0.2.1",
    "youtube_dl",
    "psutil",
    "regex",
    "pytz",
    "aiohttp",
    "python-a2s"
]

windows = []

linux = ["uvloop", "libtmux"]

darwin = []


def install(packages):
    for package in packages:
        pipmain(['install', package])


if __name__ == '__main__':
    from sys import platform

    install(_all_)
    if platform == 'windows':
        install(windows)
    if platform.startswith('linux'):
        install(linux)
    if platform == 'darwin':
        install(darwin)
