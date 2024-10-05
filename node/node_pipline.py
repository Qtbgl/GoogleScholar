import logging

import nodriver


class TaskConfig:
    browser: nodriver.Browser
    logger: logging.Logger


class ErrorToTell(Exception):
    pass
