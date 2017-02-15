import inspect
import logging
import logging.config
import os
import random
import string
import sys

from datetime import datetime

from .instance_id import SERVICE_INSTANCE_ID


# TODO: perma-cache this function
def get_relative_sys_filename(pathname):
  sys_paths = sorted(sys.path, key=len, reverse=True)
  if not sys_paths[-1]:
    sys_paths[-1] = os.getcwd()
  for sys_path in sys_paths:
    if sys_path and pathname.startswith(sys_path):
      return os.path.relpath(pathname, sys_path)
  return pathname


class OPFormatter(logging.Formatter):

  def format(self, record):
    relative_filename = get_relative_sys_filename(record.pathname)
    record.source =  "%s#%s" % (relative_filename, record.lineno)
    record.service_instance_id = SERVICE_INSTANCE_ID
    return super().format(record)

  def formatTime(self, record, datefmt=None):
    # Ignore whatever 'datefmt' is passed in
    return datetime.utcnow().isoformat() + "Z"


DEFAULT_LOG_CONFIG = {
  'version': 1,
  'disable_existing_loggers': False, # TODO: play with this...
  'formatters': {
    'op_formatter': {
      '()': OPFormatter,
      'format': '[%(asctime)s] [%(levelname)s] [%(name)s] [%(service_instance_id)s] [%(source)s]\n%(message)s'
    }
  },
  'handlers': { 
    'default': {
      'formatter': 'op_formatter',
      'class': 'logging.StreamHandler'
    },
  },
  'loggers': {
    '': {
      'handlers': ['default'],
      'level': 'NOTSET',
      'propagate': True
    }
  }
}


logging.config.dictConfig(DEFAULT_LOG_CONFIG)
