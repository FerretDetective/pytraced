# pytraced

---
**A simple, lightweight, & extensible logging library for python.**

[![PyPi](https://img.shields.io/pypi/v/pytraced)](https://pypi.org/project/pytraced/) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![Tests](https://github.com/FerretDetective/pytraced/actions/workflows/tests.yml/badge.svg)](https://github.com/FerretDetective/pytraced/actions/workflows/tests.yml) [![TypeChecking](https://github.com/FerretDetective/pytraced/actions/workflows/types.yml/badge.svg)](https://github.com/FerretDetective/pytraced/actions/workflows/types.yml) [![Linting](https://github.com/FerretDetective/pytraced/actions/workflows/lint.yml/badge.svg)](https://github.com/FerretDetective/pytraced/actions/workflows/lint.yml) [![mypy: checked](https://img.shields.io/static/v1?label=mypy&message=checked&color=green)](https://github.com/python/mypy) [![linting](https://img.shields.io/badge/linting-pylint-yellowgreen)](https://github.com/pylint-dev/pylint) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Links](#links)
- [License](#license)

## Overview

Pytraced is a simple, lightweight, & extensible logging library for python. Its aim is to provide flexible logging while maintaining the ease of use of something like using `print()`. It accomplishes this by adding numerous useful features used to configure and produce informative logs.

This library is architected around the idea of having a single logger object which all logs pass through. This is done using the top level `logger` object. Despite that, pytraced also provides the `Logger` class which can be used to further distribute and/or configure logging with more control.

## Installation

The following are instructions on the most common way and easiest ways to download & install this library.

### Installing from PyPi

To install the latest version of `pytraced` from PyPi simply pip install it using the following command.

```sh
pip install pytraced
```

### Installing from Github using Git

To install the most up-to-date version of `pytraced` from Github using Git simply run the following command.

```sh
pip install git+https://github.com/FerretDetective/pytraced
```

### Installing from Github without Git

If Git is unavailable to you, use the following instructions to download and install it from Github.

1. Navigate to [home page](https://github.com/FerretDetective/pytraced).
2. Click the green "Code" button.
3. With that menu open, click on the button labelled "Download Zip".
4. Find the downloaded zip.
5. Extract the zipped files.
6. Move the extracted folder to the desired install location.
7. Open your terminal in the location of the extracted folder.
8. Run the following command.

```sh
pip install .
```

## Basic Usage

The following are basic examples of how to the use the logger. For more information view the docstring of any functions, class, or module.

### Basic Logging

For convenience the `logger` object is configured to log to stderr by default; however this is completely configurable. The `logger` object also comes with a accompanying method for all of the built in logging levels.

```python
from pytraced import logger

# default level methods
logger.info("info")
logger.debug("debug")
logger.trace("trace")
logger.success("success")
logger.warning("warning")
logger.error("error")
logger.critical("critical")

# for logging with custom and/or dynamic levels, the `log()` method should be used
logger.log("LOG", "log")
```

### Adding New Outputs

To add new outputs to the logger the `add()` method is used. This method can be used to add callables, TextIo objects, file paths, or anything that implements `SupportsWrite[str]`. The `on_close` parameter is used to register a callback for either when the output is removed or when the interpreter exits.

```python
from pytraced import logger

OUTPUT = open("info.log", "a", encoding="utf-8")
logger.add(OUTPUT, on_remove=OUTPUT.close)  # call `close()` when this output is removed or on interpreter exit

# create the file (if necessary), and open it with the specified mode and encoding.
logger.add("logging.log", open_mode="a", encoding="utf-8")  # maintains a handle to the file during logging

# function which will be called with the formatted logging message
def log_message(message: str) -> None:
    ...

logger.add(log_message)
```

### Removing Existing Outputs

To remove an existing output from the logger the `remove()` method is used. This method takes in the id of the existing output and removes it calling the `on_remove()` callback if one was provided.

```python
from sys import stderr

from pytraced import logger

# default output is always 0
logger.remove(0)

# the id of the output is given when it is added
ID = logger.add(stderr)
logger.remove(ID)
```

### Customising the Format of Logs

To customise the format, the `add()` method is again used. This method accepts formats with the `log_format` parameter, filters using the `log_filter` parameter, a customisable minimum logging level with `min_level`, and finally the `colourise` parameter to toggle whether colours should be added to logs.

```python
from pytraced import logger, Record

# remove the default stderr output
logger.remove(0)

# disable the colouring if logs
logger.add("log.log", colourise=False)

# anything with a severity less than `ERROR` will not be logged
logger.add("log0.log", min_level="ERROR")

# customisable date-time formats, trace styles & more
logger.add("log1.log", log_format="%{time:dd/mm/yyyy, HH:MM:SS}% | %{lvl}% | %{trace:simple}% - %{msg}%")

# make your own custom formatter
def custom_formatter(record: Record) -> str:
    return f"[{record.level.name}] - {record.message}"

logger.add("log2.log", log_format=custom_formatter)

# filter your logs with a callback
SHOULD_LOG: bool = ...

def should_log(record: Record) -> bool:
    return SHOULD_LOG

logger.add("log3.log", log_filter=should_log)
```

## Links

- [Home Page](https://github.com/FerretDetective/pytraced)
- [Issue Tracker](https://github.com/FerretDetective/pytraced/issues)
- [License](https://github.com/FerretDetective/pytraced/blob/main/LICENSE.md)

## License

This project is licensed with the GNU General Public License V3, for more information view the license file which can be accessed on github located [here](https://github.com/FerretDetective/pytraced/blob/main/LICENSE.md).
