# -*- coding: utf-8 -*-
#
# 2010-2013 Nico Schottelius (nico-cdist at schottelius.org)
# 2019-2020 Steven Armstrong
# 2021 Dennis Camera (cdist at dtnr.ch)
#
# This file is part of cdist.
#
# cdist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# cdist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with cdist. If not, see <http://www.gnu.org/licenses/>.
#
#

import collections
import datetime
import logging
import logging.handlers
import os
import sys

from logging import *

root = logging.root

# Define additional cdist logging levels.
logging.OFF = logging.CRITICAL + 10  # disable logging
logging.addLevelName(logging.OFF, 'OFF')


logging.VERBOSE = logging.INFO - 5
logging.addLevelName(logging.VERBOSE, 'VERBOSE')


def _verbose(self, msg, *args, **kwargs):
    self.log(logging.VERBOSE, msg, args, **kwargs)


logging.Logger.verbose = _verbose


logging.TRACE = logging.DEBUG - 5
logging.addLevelName(logging.TRACE, 'TRACE')


def _trace(self, msg, *args, **kwargs):
    self.log(logging.TRACE, msg, *args, **kwargs)


logging.Logger.trace = _trace


_verbosity_level_off = -2

# All verbosity levels above 4 are TRACE.
_verbosity_level = collections.defaultdict(lambda: logging.TRACE, {
    None: logging.WARNING,
    _verbosity_level_off: logging.OFF,
    -1: logging.ERROR,
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.VERBOSE,
    3: logging.DEBUG,
    4: logging.TRACE,
    })

# Generate verbosity level constants:
# VERBOSE_OFF, VERBOSE_ERROR, VERBOSE_WARNING, VERBOSE_INFO, VERBOSE_VERBOSE,
# VERBOSE_DEBUG, VERBOSE_TRACE.
globals().update({
    ("VERBOSE_" + logging.getLevelName(l)): i
    for i, l in _verbosity_level.items()
    if i is not None
    })


class CdistFormatter(logging.Formatter):
    USE_COLORS = False
    RESET = '\033[0m'
    COLOR_MAP = {
        'ERROR': '\033[0;31m',
        'WARNING': '\033[0;33m',
        'INFO': '\033[0;94m',
        'VERBOSE': '\033[0;34m',
        'DEBUG': '\033[0;90m',
        'TRACE': '\033[0;37m',
    }

    def __init__(self, fmt):
        super().__init__(fmt=fmt)

    def format(self, record):
        msg = super().format(record)
        if self.USE_COLORS:
            color = self.COLOR_MAP.get(record.levelname)
            if color:
                msg = color + msg + self.RESET
        return msg


class DefaultLog(logging.Logger):
    FORMAT = '%(levelname)s: %(name)s: %(message)s'

    class StdoutFilter(logging.Filter):
        def filter(self, rec):
            return rec.levelno != logging.ERROR

    class StderrFilter(logging.Filter):
        def filter(self, rec):
            return rec.levelno == logging.ERROR

    def __init__(self, name):
        super().__init__(name)
        self.propagate = False

        formatter = CdistFormatter(self.FORMAT)

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.addFilter(self.StdoutFilter())
        stdout_handler.setLevel(logging.TRACE)
        stdout_handler.setFormatter(formatter)

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.addFilter(self.StderrFilter())
        stderr_handler.setLevel(logging.ERROR)
        stderr_handler.setFormatter(formatter)

        self.addHandler(stdout_handler)
        self.addHandler(stderr_handler)

    def verbose(self, msg, *args, **kwargs):
        self.log(logging.VERBOSE, msg, *args, **kwargs)

    def trace(self, msg, *args, **kwargs):
        self.log(logging.TRACE, msg, *args, **kwargs)


class TimestampingLog(DefaultLog):

    def filter(self, record):
        """Add timestamp to messages"""

        super().filter(record)
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S.%f")
        record.msg = "[" + timestamp + "] " + str(record.msg)

        return True


class ParallelLog(DefaultLog):
    FORMAT = '%(levelname)s: [%(process)d]: %(name)s: %(message)s'


class TimestampingParallelLog(TimestampingLog, ParallelLog):
    pass


def setupDefaultLogging():
    del logging.getLogger().handlers[:]
    logging.setLoggerClass(DefaultLog)


def setupTimestampingLogging():
    del logging.getLogger().handlers[:]
    logging.setLoggerClass(TimestampingLog)


def setupTimestampingParallelLogging():
    del logging.getLogger().handlers[:]
    logging.setLoggerClass(TimestampingParallelLog)


def setupParallelLogging():
    del logging.getLogger().handlers[:]
    logging.setLoggerClass(ParallelLog)


setupDefaultLogging()
