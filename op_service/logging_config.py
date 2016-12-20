import logging.config
from datetime import datetime


class UTCFormatter(logging.Formatter):

  def formatTime(self, record, datefmt=None):
    # Ignore whatever 'datefmt' is passed in
    return datetime.utcnow().isoformat() + "Z"


DEFAULT_LOG_CONFIG = {
  'version': 1,
  'disable_existing_loggers': False,
  'formatters': {
    'utc_formatter': {
      '()': UTCFormatter,
      'format': '[%(asctime)s] [%(levelname)s] [%(name)s] [%(pathname)s#%(lineno)s]\n%(message)s'
    }
  },
  'handlers': { 
    'default': {
      'formatter': 'utc_formatter',
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
