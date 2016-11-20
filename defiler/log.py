import logging
import logging.config

def configure_logging(debug):
    LOGGING = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s %(name)s:"
                          "%(levelname)s: %(message)s "
                          "(%(filename)s:%(lineno)d)",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": "DEBUG"
            }
        }
    }

    if debug:
        LOGGING["handlers"]["console"]["level"] = "DEBUG"
    else:
        LOGGING["loggers"][""]["handlers"].remove("console")

    def _get_handler(key, value):
        return {
            "level": key.upper(),
            "filename": value,
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard"
        }

    logging.config.dictConfig(LOGGING)
