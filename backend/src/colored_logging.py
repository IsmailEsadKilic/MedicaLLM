"""
Colored logging formatter for console output.
File logs remain plain text for easier parsing.
"""
import logging
import sys


class Colors:
    """ANSI color codes for terminal output."""
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    
    # High intensity colors
    HBLACK = '\033[90m'
    HRED = '\033[91m'
    HGREEN = '\033[92m'
    HYELLOW = '\033[93m'
    HBLUE = '\033[94m'
    HMAGENTA = '\033[95m'
    HCYAN = '\033[96m'
    HWHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to console output based on log level.
    
    Color scheme:
    - DEBUG: Purple/Magenta (🐛)
    - INFO: Cyan (🤓)
    - SUCCESS: Green (🥹) - custom level
    - WARNING: Yellow/Orange (😳)
    - ERROR: Red (😱)
    - CRITICAL: Bold Red (💀)
    """
    
    # Define colors for each log level
    LEVEL_COLORS = {
        'DEBUG': Colors.HMAGENTA,
        'INFO': Colors.HCYAN,
        'SUCCESS': Colors.HGREEN,
        'WARNING': Colors.HYELLOW,
        'ERROR': Colors.HRED,
        'CRITICAL': f"{Colors.BOLD}{Colors.HRED}",
    }
    
    # Define background colors for level names
    LEVEL_BG_COLORS = {
        'DEBUG': Colors.BG_MAGENTA,
        'INFO': Colors.BG_CYAN,
        'SUCCESS': Colors.BG_GREEN,
        'WARNING': Colors.BG_YELLOW,
        'ERROR': Colors.BG_RED,
        'CRITICAL': Colors.BG_RED,
    }
    
    # Emojis for each level
    LEVEL_EMOJIS = {
        'DEBUG': '🐛',
        'INFO': '🤓',
        'SUCCESS': '🥹',
        'WARNING': '😳',
        'ERROR': '😱',
        'CRITICAL': '💀',
    }
    
    def __init__(self, fmt=None, datefmt=None, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and self._supports_color()
    
    @staticmethod
    def _supports_color():
        """
        Check if the terminal supports colors.
        Returns True if running in a terminal that supports ANSI colors.
        """
        # Check if stdout is a terminal
        if not hasattr(sys.stdout, 'isatty'):
            return False
        if not sys.stdout.isatty():
            return False
        
        # Windows check
        try:
            import platform
            if platform.system() == 'Windows':
                # Enable ANSI colors on Windows 10+
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
        except:
            pass
        
        return True
    
    def format(self, record):
        if not self.use_colors:
            return super().format(record)
        
        # Get the log level name
        levelname = record.levelname
        
        # Get colors for this level
        level_color = self.LEVEL_COLORS.get(levelname, Colors.HWHITE)
        level_bg_color = self.LEVEL_BG_COLORS.get(levelname, Colors.BG_BLACK)
        emoji = self.LEVEL_EMOJIS.get(levelname, '📝')
        
        # Color the level name with background
        colored_levelname = f"{level_bg_color}[{levelname}{emoji}]{Colors.ENDC}"
        
        # Color the message
        colored_message = f"{level_color}{record.getMessage()}{Colors.ENDC}"
        
        # Format timestamp
        if self.datefmt:
            timestamp = self.formatTime(record, self.datefmt)
        else:
            timestamp = self.formatTime(record)
        
        # Color timestamp in gray
        colored_timestamp = f"{Colors.HBLACK}{timestamp}{Colors.ENDC}"
        
        # Build the final log message
        log_message = f"{colored_timestamp} - {colored_levelname} {colored_message}"
        
        # Add exception info if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            # Color exception in red
            colored_exc = f"{Colors.HRED}{exc_text}{Colors.ENDC}"
            log_message = f"{log_message}\n{colored_exc}"
        
        return log_message


# Add custom SUCCESS log level
SUCCESS_LEVEL = 25  # Between INFO (20) and WARNING (30)
logging.addLevelName(SUCCESS_LEVEL, 'SUCCESS')


def success(self, message, *args, **kwargs):
    """Log a success message."""
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Add success method to Logger class
logging.Logger.success = success


def setup_colored_logging(
    log_level=logging.DEBUG,
    log_file=None,
    log_format="%(asctime)s - %(levelname)s - %(message)s",
    date_format=None,
):
    """
    Setup logging with colored console output and plain file output.
    
    Args:
        log_level: Logging level (default: DEBUG)
        log_file: Path to log file (optional)
        log_format: Log message format
        date_format: Date format for timestamps
    
    Returns:
        Configured logger instance
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(log_format, date_format, use_colors=True)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler without colors (plain text)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


# Convenience functions for colored logging
def get_colored_logger(name):
    """Get a logger instance with colored output."""
    return logging.getLogger(name)
