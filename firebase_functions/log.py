"""Module for a logger that formats output correctly for Cloud Logging."""

import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SingleLevelFilter(logging.Filter):

  def __init__(self, passlevel, reject):
    self.passlevel = passlevel
    self.reject = reject

  def filter(self, record):
    if self.reject:
      return record.levelno != self.passlevel
    else:
      return record.levelno == self.passlevel


# class JSONFormatter(logging.Formatter):


def debug(*args, sep=''):
  debug_log = logging.StreamHandler(sys.stdout)
  debug_filter = SingleLevelFilter(logging.INFO, False)
  debug_log.addFilter(debug_filter)
  root_logger = logging.getLogger()
  root_logger.addHandler(debug_log)
  logger.setLevel(logging.DEBUG)
  logger.debug(args)


def info(*args, sep=''):
  logger.info(args)


def warn(*args, sep=''):
  logger.warning(args)


def error(*args, sep=''):
  logger.error(args)
