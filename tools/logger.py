import logging
import sys

def get_logger(name):
    """
    Returns a structured logger with timestamps, severity levels, 
    and module names in a consistent format.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Consistent format: YYYY-MM-DD HH:MM:SS - NAME - LEVEL - MESSAGE
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Direct logs to stderr (as per V5 plan)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger
