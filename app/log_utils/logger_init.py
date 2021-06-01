# Source: https://github.com/civicsoft/ieddit/blob/master/app/utilities/log_utils/logger_init.py
import os

# Setup For Logging Init
import yaml
import logging
import app.log_utils.logger_util

# Pull in Logging Config
path = os.path.join(os.getcwd(), 'app', 'log_utils', 'logger_config.yaml')
with open(path, 'r') as stream:
    try:
      logging_config = yaml.load(stream, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
      print("Error Loading Logger Config")
      pass

# Load Logging configs
logging.config.dictConfig(logging_config)

# Initialize Log Levels
# log_level = logging.DEBUG


# Set the logging level for all loggers in scope 
# This level can be overwritten by the following in a file
#   logger = logging.getlogger(__name__)
#   logger.setLevel(logging.INFO)

# The following sets the log_level for all loggers
# loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
# for log in loggers:
#   log.setLevel(log_level)

