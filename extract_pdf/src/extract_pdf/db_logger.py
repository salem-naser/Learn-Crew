"""
Database logger for task execution tracking.
Uses SQLAlchemy with SQLite for persistent task and workflow logging.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from extract_pdf.logging_config import get_logger

Base = declarative_base()
logger = get_logger('db')


class WorkflowRun(Base):
    """Represents a single workflow execution."""
    __tablename__ = 'workflow_runs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), unique=True, nullable=False, index=True)
    pdf_path = Column(String(500))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50), default='running')  # running, completed, failed
    total_duration = Column(Float)
    user_guid = Column(String(36))
    error_message = Column(Text)
    metadata = Column(Text)  # JSON string for additional data
    
    # Relationships
    tasks = relationship('TaskExecution', back_populates='workflow', cascade='all, delete-orphan')
    validations = relationship('ValidationLog', back_populates='workflow', cascade='all, delete-orphan')
    api_calls = relationship('APICallLog', back_populates='workflow', cascade='all, delete-orphan')


class TaskExecution(Base):
    """Tracks individual task executions within a workflow."""
    __tablename__ = 'task_executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id = Column(Integer, ForeignKey('workflow_runs.id'), nullable=False)
    task_name = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50), default='running')  # running, completed, failed
    duration = Column(Float)
    input_summary = Column(Text)
    output_summary = Column(Text)
    output_file = Column(String(500))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    workflow = relationship('WorkflowRun', back_populates='tasks')


class ValidationLog(Base):
    """Logs validation results from Guardrails or JSON Schema."""
    __tablename__ = 'validation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id = Column(Integer, ForeignKey('workflow_runs.id'), nullable=False)
    task_name = Column(String(100))
    validator_type = Column(String(50))  # guardrails, jsonschema
    schema_name = Column(String(100))
    is_valid = Column(Boolean, default=False)
    validated_at = Column(DateTime, default=datetime.utcnow)
    error_count = Column(Integer, default=0)
    errors = Column(Text)  # JSON array of error messages
    warnings = Column(Text)  # JSON array of warning messages
    corrections_applied = Column(Text)  # JSON of auto-corrections by Guardrails
    raw_input = Column(Text)
    corrected_output = Column(Text)
    
    # Relationships
    workflow = relationship('WorkflowRun', back_populates='validations')


class APICallLog(Base):
    """Logs API call details and responses."""
    __tablename__ = 'api_call_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id = Column(Integer, ForeignKey('workflow_runs.id'), nullable=False)
    endpoint_name = Column(String(100))  # user_endpoint, medication_endpoint
    url = Column(String(500))
    method = Column(String(10), default='POST')
    called_at = Column(DateTime, default=datetime.utcnow)
    response_code = Column(Integer)
    response_time = Column(Float)  # in seconds
    is_success = Column(Boolean, default=False)
    request_body_summary = Column(Text)
    response_body_summary = Column(Text)
    error_message = Column(Text)
    headers_sent = Column(Text)  # JSON without sensitive data
    
    # Relationships
    workflow = relationship('WorkflowRun', back_populates='api_calls')


class DatabaseLogger:
    """
    Database logger for tracking workflow and task execution.
    Uses SQLite by default, can be configured for PostgreSQL.
    """
    
    _instance = None
    _engine = None
    _SessionFactory = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: Optional[str] = None, db_url: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: ./data/workflow.db)
            db_url: Full database URL for PostgreSQL or other databases
        """
        if DatabaseLogger._engine is not None:
            return
        
        if db_url:
            connection_string = db_url
        else:
            if db_path is None:
                db_dir = Path(__file__).parent.parent.parent / 'data'
            else:
                db_dir = Path(db_path).parent
            
            db_dir.mkdir(parents=True, exist_ok=True)
            db_file = db_dir / 'workflow.db' if db_path is None else Path(db_path)
            connection_string = f'sqlite:///{db_file}'
        
        DatabaseLogger._engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True
        )
        
        # Create tables
        Base.metadata.create_all(DatabaseLogger._engine)
        
        DatabaseLogger._SessionFactory = sessionmaker(bind=DatabaseLogger._engine)
        
        logger.info(f"Database initialized: {connection_string}")
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = DatabaseLogger._SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def create_workflow_run(
        self,
        run_id: str,
        pdf_path: str,
        metadata: Dict[str, Any] = None
    ) -> WorkflowRun:
        """Create a new workflow run record."""
        with self.session_scope() as session:
            workflow = WorkflowRun(
                run_id=run_id,
                pdf_path=pdf_path,
                status='running',
                metadata=json.dumps(metadata) if metadata else None
            )
            session.add(workflow)
            session.flush()
            logger.info(f"Workflow run created: {run_id}")
            return workflow.id
    
    def update_workflow_status(
        self,
        run_id: str,
        status: str,
        user_guid: str = None,
        error_message: str = None
    ) -> None:
        """Update workflow run status."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if workflow:
                workflow.status = status
                workflow.completed_at = datetime.utcnow()
                workflow.total_duration = (
                    workflow.completed_at - workflow.started_at
                ).total_seconds()
                if user_guid:
                    workflow.user_guid = user_guid
                if error_message:
                    workflow.error_message = error_message
                logger.info(f"Workflow {run_id} status updated to: {status}")
    
    def log_task_execution(
        self,
        run_id: str,
        task_name: str,
        agent_name: str = None,
        status: str = 'running',
        input_summary: str = None,
        output_summary: str = None,
        output_file: str = None,
        error_message: str = None,
        duration: float = None
    ) -> int:
        """Log a task execution event."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow:
                logger.warning(f"Workflow {run_id} not found for task logging")
                return None
            
            task = TaskExecution(
                workflow_run_id=workflow.id,
                task_name=task_name,
                agent_name=agent_name,
                status=status,
                input_summary=input_summary[:1000] if input_summary else None,
                output_summary=output_summary[:1000] if output_summary else None,
                output_file=output_file,
                error_message=error_message,
                duration=duration
            )
            
            if status in ['completed', 'failed']:
                task.completed_at = datetime.utcnow()
            
            session.add(task)
            session.flush()
            logger.info(f"Task logged: {task_name} ({status})")
            return task.id
    
    def update_task_status(
        self,
        run_id: str,
        task_name: str,
        status: str,
        output_summary: str = None,
        error_message: str = None,
        duration: float = None
    ) -> None:
        """Update an existing task's status."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow:
                return
            
            task = session.query(TaskExecution).filter_by(
                workflow_run_id=workflow.id,
                task_name=task_name
            ).order_by(TaskExecution.id.desc()).first()
            
            if task:
                task.status = status
                task.completed_at = datetime.utcnow()
                if output_summary:
                    task.output_summary = output_summary[:1000]
                if error_message:
                    task.error_message = error_message
                if duration:
                    task.duration = duration
    
    def log_validation(
        self,
        run_id: str,
        task_name: str,
        validator_type: str,
        schema_name: str,
        is_valid: bool,
        errors: List[str] = None,
        warnings: List[str] = None,
        corrections: Dict[str, Any] = None,
        raw_input: str = None,
        corrected_output: str = None
    ) -> int:
        """Log a validation result."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow:
                return None
            
            validation = ValidationLog(
                workflow_run_id=workflow.id,
                task_name=task_name,
                validator_type=validator_type,
                schema_name=schema_name,
                is_valid=is_valid,
                error_count=len(errors) if errors else 0,
                errors=json.dumps(errors) if errors else None,
                warnings=json.dumps(warnings) if warnings else None,
                corrections_applied=json.dumps(corrections) if corrections else None,
                raw_input=raw_input[:5000] if raw_input else None,
                corrected_output=corrected_output[:5000] if corrected_output else None
            )
            
            session.add(validation)
            session.flush()
            
            log_msg = f"Validation logged: {schema_name} - {'PASS' if is_valid else 'FAIL'}"
            if is_valid:
                logger.info(log_msg)
            else:
                logger.warning(log_msg)
            
            return validation.id
    
    def log_api_call(
        self,
        run_id: str,
        endpoint_name: str,
        url: str,
        method: str = 'POST',
        response_code: int = None,
        response_time: float = None,
        is_success: bool = False,
        request_summary: str = None,
        response_summary: str = None,
        error_message: str = None
    ) -> int:
        """Log an API call."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow:
                return None
            
            api_call = APICallLog(
                workflow_run_id=workflow.id,
                endpoint_name=endpoint_name,
                url=url,
                method=method,
                response_code=response_code,
                response_time=response_time,
                is_success=is_success,
                request_body_summary=request_summary[:2000] if request_summary else None,
                response_body_summary=response_summary[:2000] if response_summary else None,
                error_message=error_message
            )
            
            session.add(api_call)
            session.flush()
            
            log_msg = f"API call logged: {endpoint_name} -> {response_code}"
            if is_success:
                logger.info(log_msg)
            else:
                logger.warning(log_msg)
            
            return api_call.id
    
    def get_workflow_summary(self, run_id: str) -> Dict[str, Any]:
        """Get a summary of a workflow run."""
        with self.session_scope() as session:
            workflow = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow:
                return None
            
            tasks = session.query(TaskExecution).filter_by(
                workflow_run_id=workflow.id
            ).all()
            
            validations = session.query(ValidationLog).filter_by(
                workflow_run_id=workflow.id
            ).all()
            
            api_calls = session.query(APICallLog).filter_by(
                workflow_run_id=workflow.id
            ).all()
            
            return {
                'run_id': workflow.run_id,
                'pdf_path': workflow.pdf_path,
                'status': workflow.status,
                'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
                'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
                'total_duration': workflow.total_duration,
                'user_guid': workflow.user_guid,
                'tasks': [
                    {
                        'name': t.task_name,
                        'agent': t.agent_name,
                        'status': t.status,
                        'duration': t.duration
                    }
                    for t in tasks
                ],
                'validations': [
                    {
                        'schema': v.schema_name,
                        'is_valid': v.is_valid,
                        'errors': json.loads(v.errors) if v.errors else []
                    }
                    for v in validations
                ],
                'api_calls': [
                    {
                        'endpoint': a.endpoint_name,
                        'status_code': a.response_code,
                        'success': a.is_success,
                        'response_time': a.response_time
                    }
                    for a in api_calls
                ]
            }
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow runs."""
        with self.session_scope() as session:
            workflows = session.query(WorkflowRun).order_by(
                WorkflowRun.started_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    'run_id': w.run_id,
                    'pdf_path': w.pdf_path,
                    'status': w.status,
                    'started_at': w.started_at.isoformat() if w.started_at else None,
                    'duration': w.total_duration
                }
                for w in workflows
            ]


# Global instance for convenience
_db_logger: Optional[DatabaseLogger] = None


def get_db_logger(db_path: str = None) -> DatabaseLogger:
    """Get or create the global database logger instance."""
    global _db_logger
    if _db_logger is None:
        _db_logger = DatabaseLogger(db_path=db_path)
    return _db_logger
