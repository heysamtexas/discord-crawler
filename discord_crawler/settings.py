"""Config file for logging and other settings as they come along."""
import os


VERBOSE = os.getenv('VERBOSE', False)
LOG_LEVEL = os.environ['LOG_LEVEL']

DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(module)s %(levelname)s: %(message)s',
        },
    },
    'handlers': {
        'default':  {
            'level': 'DEBUG',
            'formatter': "standard",
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'WARNING',
            'propagate': False
        },
        'libs': {
            'handlers': ['default'],
            'level': LOG_LEVEL,
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': LOG_LEVEL,
            'propagate': False
        },
    }
}

BASE_URL = 'https://discord.com/api/v10/{0}'

USER_AGENT = os.getenv('USER_AGENT', 'MeBottt (https://mebottt.co, 0.1)')
DATABASE_URI = os.environ['DATABASE_URL']