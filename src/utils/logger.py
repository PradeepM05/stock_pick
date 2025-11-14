"""
Logger Configuration
Sets up consistent logging across the application
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = 'stock_screener',
    level: str = 'INFO',
    log_file: bool = True,
    log_dir: Path = None
) -> logging.Logger:
    """
    Setup and configure logger
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Whether to write logs to file
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with UTF-8 encoding for cross-platform support
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Set UTF-8 encoding on Windows to handle Unicode characters
    if sys.platform == 'win32':
        try:
            import codecs
            # Wrap stdout with UTF-8 encoding
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
        except (AttributeError, OSError):
            # If wrapping fails, continue with default encoding
            # Unicode characters will be replaced with '?'
            pass
    
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs'
        
        log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file_path = log_dir / f'{name}_{timestamp}.log'
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file_path}")
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get existing logger or create new one
    
    Args:
        name: Logger name (defaults to stock_screener)
        
    Returns:
        Logger instance
    """
    if name is None:
        name = 'stock_screener'
    
    logger = logging.getLogger(name)
    
    # Setup if not already configured
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Create default logger on import
default_logger = setup_logger()
