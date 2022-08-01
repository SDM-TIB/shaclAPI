import logging

from multiprocessing_logging import install_mp_handler


def setup(handler=logging.StreamHandler(), level=logging.INFO, format='[%(asctime)s - %(levelname)s] %(name)s - %(processName)s: %(msg)s'):
    """Sets up the logger of the shaclAPI. Has to be used before importing shaclapi.api.

    Parameters
    ----------
        handler : logging.Handler, optional
            The handler to be used for logging of the shaclapi
        level : logging._LEVEL, optional
            The logging level
        format : str, optional
            The format to be used during logging.
    """
    handler.setFormatter(logging.Formatter(format))
    handler.setLevel(level)
    logger = logging.getLogger('shaclapi')
    logger.addHandler(handler)
    logger.setLevel(level)
    install_mp_handler(logger)
    print('shaclAPI logger assigned!')
