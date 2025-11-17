import logging
import sys
import os
from logging.config import dictConfig

# Define a function to configure logging
def configure_logging() -> None:
  log_level = os.getenv("LOG_LEVEL", "INFO").upper()

  # Define the logging configuration dictionary
  log_config = {
      "version": 1,
      "disable_existing_loggers": False,
      "formatters": {
          "default": {
              "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
              "datefmt": "%Y-%m-%d %H:%M:%S",
          },
          "json": {
              "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
              "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(user_email)s %(db_query_time)s",
          },
      },
      "handlers": {
          "console": {
              "class": "logging.StreamHandler",
              "level": log_level,
              "formatter": "json",
              "stream": sys.stdout,
          },
      },
      "root": {
          "handlers": ["console"],
          "level": log_level,
      },
      "loggers": {
          "uvicorn": {
              "level": "INFO",
              "handlers": ["console"],
              "propagate": False,
          },
          "uvicorn.error": {
              "level": "INFO",
              "handlers": ["console"],
              "propagate": False,
          },
          "uvicorn.access": {
              "level": "INFO",
              "handlers": ["console"],
              "propagate": False,
          },
      },
  }

  # Apply the logging configuration
  dictConfig(log_config)


# Helper function to log SQLAlchemy queries with execution time (useful for debugging DB performance)
def log_sqlalchemy_queries(sqlalchemy_engine) -> None:
  """
  Attach a listener to log SQLAlchemy queries (SQL and execution time).
  """
  from sqlalchemy import event

  @event.listens_for(sqlalchemy_engine, "after_cursor_execute")
  def after_cursor_execute(
      conn, cursor, statement, parameters, context, executemany
  ):
    if context:
      db_query_time = context.get("duration")
      if db_query_time:
        # Add db_query_time to log
        extra = {"db_query_time": f"{db_query_time:.2f}ms"}
        logger = logging.getLogger("sqlalchemy.engine")
        logger.info(f"Executed SQL: {statement}", extra=extra)


# Call this function in app.main to ensure the SQLAlchemy query logger is active
def setup_sqlalchemy_logging(db_engine) -> None:
  """
  Setup SQLAlchemy query logging for performance analysis and debugging.
  This will log all queries with their execution time in milliseconds.
  """
  log_sqlalchemy_queries(db_engine)


# --- Logger Setup ---
# Setup the logger for the app
logger = logging.getLogger("app")

# Configure the logger at the start of your application (e.g., in main.py)
# You can call this from app.main to set up logging
if __name__ == "__main__":
  configure_logging()

  # Example log at startup
  logger.info("Logging is configured.")
