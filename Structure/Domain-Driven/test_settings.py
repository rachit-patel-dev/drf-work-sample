# Import settings from main settings.py file
from .settings import *

# Disable logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
}
