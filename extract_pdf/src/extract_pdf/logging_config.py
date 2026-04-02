"""
Logging configuration for Extract PDF Crew.
Provides structured logging to console and files with rotation.
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggingConfig:
    """Centralized logging configuration for the Extract PDF workflow."""
    
    _initialized = False
    _loggers = {}
    
    # Log levels mapping
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    @classmethod
    def setup(
        cls,
        log_dir: Optional[str] = None,
        console_level: str = 'INFO',
        file_level: str = 'DEBUG',
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """
        Initialize logging configuration.
        
        Args:
            log_dir: Directory to store log files. Defaults to ./logs
            console_level: Minimum log level for console output
            file_level: Minimum log level for file output
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup files to keep
        """
        if cls._initialized:
            return
            
        # Create logs directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / 'logs'
        else:
            log_dir = Path(log_dir)
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        json_formatter = JsonFormatter()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(cls.LEVELS.get(console_level, logging.INFO))
        console_handler.setFormatter(console_formatter)
        
        # Main application log (rotating)
        app_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'app.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(cls.LEVELS.get(file_level, logging.DEBUG))
        app_handler.setFormatter(detailed_formatter)
        
        # Validation log
        validation_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'validation.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        validation_handler.setLevel(logging.DEBUG)
        validation_handler.setFormatter(detailed_formatter)
        
        # API log
        api_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'api.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(detailed_formatter)
        
        # Tasks log (JSON format for structured analysis)
        tasks_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'tasks.json.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        tasks_handler.setLevel(logging.DEBUG)
        tasks_handler.setFormatter(json_formatter)
        
        # Error log (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'errors.log',
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger('extract_pdf')
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(app_handler)
        root_logger.addHandler(error_handler)
        
        # Configure specialized loggers
        validation_logger = logging.getLogger('extract_pdf.validation')
        validation_logger.addHandler(validation_handler)
        
        api_logger = logging.getLogger('extract_pdf.api')
        api_logger.addHandler(api_handler)
        
        tasks_logger = logging.getLogger('extract_pdf.tasks')
        tasks_logger.addHandler(tasks_handler)
        
        cls._initialized = True
        cls._loggers = {
            'main': root_logger,
            'validation': validation_logger,
            'api': api_logger,
            'tasks': tasks_logger
        }
        
        root_logger.info("Logging initialized successfully")
    
    @classmethod
    def get_logger(cls, name: str = 'main') -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name ('main', 'validation', 'api', 'tasks')
            
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup()
        
        if name in cls._loggers:
            return cls._loggers[name]
        
        # Create child logger
        return logging.getLogger(f'extract_pdf.{name}')


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        # Add extra fields if present
        if hasattr(record, 'task_name'):
            log_entry['task_name'] = record.task_name
        if hasattr(record, 'agent_name'):
            log_entry['agent_name'] = record.agent_name
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
        if hasattr(record, 'status'):
            log_entry['status'] = record.status
        if hasattr(record, 'input_data'):
            log_entry['input_data'] = record.input_data
        if hasattr(record, 'output_data'):
            log_entry['output_data'] = record.output_data
        if hasattr(record, 'error'):
            log_entry['error'] = record.error
            
        # Include exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


# Convenience functions
def get_logger(name: str = 'main') -> logging.Logger:
    """Get a logger instance."""
    return LoggingConfig.get_logger(name)


def setup_logging(**kwargs) -> None:
    """Initialize logging configuration."""
    LoggingConfig.setup(**kwargs)


def log_task_event(
    task_name: str,
    status: str,
    agent_name: str = None,
    duration: float = None,
    input_summary: str = None,
    output_summary: str = None,
    error: str = None
) -> None:
    """
    Log a task execution event with structured data.
    
    Args:
        task_name: Name of the task
        status: Task status (started, completed, failed)
        agent_name: Name of the agent executing the task
        duration: Execution duration in seconds
        input_summary: Summary of input data
        output_summary: Summary of output data
        error: Error message if task failed
    """
    logger = get_logger('tasks')
    
    # Create log record with extra fields
    extra = {
        'task_name': task_name,
        'status': status
    }
    
    if agent_name:
        extra['agent_name'] = agent_name
    if duration is not None:
        extra['duration'] = duration
    if input_summary:
        extra['input_data'] = input_summary
    if output_summary:
        extra['output_data'] = output_summary
    if error:
        extra['error'] = error
    
    level = logging.ERROR if status == 'failed' else logging.INFO
    logger.log(level, f"Task '{task_name}' {status}", extra=extra)
