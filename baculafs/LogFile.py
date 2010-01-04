import logging
import logging.handlers

LOGGING_LEVELS = {'debug': logging.DEBUG,
                  'info': logging.INFO,
                  'warning': logging.WARNING,
                  'error': logging.ERROR,
                  'critical': logging.CRITICAL}

class LogFile :
    '''
    file like object that wraps a logger object
    '''
    def __init__(self, logger, level) :
        self.logger = logger
        self.level = level

    def write(self, message) :
        for line in message.splitlines() :
            self.logger.log(self.level, line)

    def flush(self) :
        for handler in self.logger.handlers :
            handler.flush()
        

