"""
SAE AI Training Center

Manages datasets, training jobs, checkpoints, and evaluation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from .models import (
    Dataset, DatasetStatus, TrainingJob, TrainingStatus,
    TrainingType, Checkpoint, EvaluationRun, Experiment
)

logger = logging.getLogger(__name__)


class DatasetRegistry:
    """Registry for datasets."""
    
    def __init__(self):
        self.datasets: Dict[str, Dataset] = {}
    
    def register_dataset(self, dataset: Dataset) -> None:
        """Register a new dataset."""
        if dataset.id in self.datasets:
            raise ValueError(f"Dataset {dataset.id} already registered")
        
        self.datasets[dataset.id] = dataset
        logger.info(f"Dataset registered: {dataset.id} ({dataset.name})")
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID."""
        return self.datasets.get(dataset_id)
    
    def validate_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Validate dataset.
        
        In real implementation, would check:
        - Schema compliance
        - Missing data
        - Shape/dtype
        - NaN/Inf
        - Duplicates
        - Labels
        - Class distribution
        - Train/val/test split
        - Data leakage
        - Provenance
        - License metadata
        """
        dataset = self.datasets.get(dataset_id)
        if not dataset:
            return {"valid": False, "errors": ["Dataset not found"]}
        
        errors = []
        warnings = []
        
        # Basic validation
        if not dataset.name:
            errors.append("Dataset name is required")
        
        if not dataset.location:
            errors.append("Dataset location is required")
        
        if not dataset.format:
            errors.append("Dataset format is required")
        
        # Update status
        if errors:
            dataset.validation_status = DatasetStatus.INVALID
        else:
            dataset.validation_status = DatasetStatus.VALID
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def list_datasets(
        self,
        status: Optional[DatasetStatus] = None,
        modality: Optional[str] = None
    ) -> List[Dataset]:
        """List datasets with optional filters."""
        datasets = list(self.datasets.values())
        
        if status:
            datasets = [d for d in datasets if d.validation_status == status]
        
        if modality:
            datasets = [d for d in datasets if d.modality == modality]
        
        return datasets


class CheckpointManager:
    """Manages model checkpoints."""
    
    def __init__(self):
        self.checkpoints: Dict[str, Checkpoint] = {}
    
    def register_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Register a new checkpoint."""
        if checkpoint.id in self.checkpoints:
            raise ValueError(f"Checkpoint {checkpoint.id} already registered")
        
        self.checkpoints[checkpoint.id] = checkpoint
        logger.info(f"Checkpoint registered: {checkpoint.id} for model {checkpoint.model_id}")
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)
    
    def get_checkpoints_by_model(self, model_id: str) -> List[Checkpoint]:
        """Get all checkpoints for a model."""
        return [
            cp for cp in self.checkpoints.values()
            if cp.model_id == model_id
        ]
    
    def get_latest_checkpoint(self, model_id: str) -> Optional[Checkpoint]:
        """Get latest checkpoint for a model."""
        checkpoints = self.get_checkpoints_by_model(model_id)
        if not checkpoints:
            return None
        
        return max(checkpoints, key=lambda cp: cp.created_at)
    
    def verify_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Verify checkpoint integrity.
        
        In real implementation, would:
        - Check file exists
        - Verify hash
        - Load and validate structure
        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        if not checkpoint:
            return {"valid": False, "error": "Checkpoint not found"}
        
        # In real implementation, would verify file and hash
        return {
            "valid": True,
            "checkpoint": checkpoint
        }


class TrainingCenter:
    """
    Main training center for AI model training.
    
    Manages training jobs, datasets, checkpoints, and evaluation.
    """
    
    def __init__(
        self,
        dataset_registry: DatasetRegistry,
        checkpoint_manager: CheckpointManager,
        approval_engine=None,
        audit_engine=None
    ):
        self.dataset_registry = dataset_registry
        self.checkpoint_manager = checkpoint_manager
        self.approval_engine = approval_engine
        self.audit_engine = audit_engine
        
        self.training_jobs: Dict[str, TrainingJob] = {}
        self.evaluation_runs: Dict[str, EvaluationRun] = {}
        self.experiments: Dict[str, Experiment] = {}
    
    def create_training_job(
        self,
        model_id: str,
        base_model: str,
        dataset_id: str,
        training_type: TrainingType,
        config: Dict[str, Any],
        requested_by: str,
        device: str = "cpu",
        precision: str = "fp32"
    ) -> TrainingJob:
        """
        Create a new training job.
        
        Args:
            model_id: Target model ID
            base_model: Base model ID
            dataset_id: Dataset ID
            training_type: Type of training
            config: Training configuration
            requested_by: User ID
            device: Training device
            precision: Training precision
        
        Returns:
            TrainingJob
        """
        # Validate dataset
        dataset = self.dataset_registry.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        if dataset.validation_status != DatasetStatus.VALID:
            raise ValueError(f"Dataset {dataset_id} is not valid (status: {dataset.validation_status})")
        
        # Create training job
        job = TrainingJob(
            id=f"train_{datetime.utcnow().timestamp()}",
            model_id=model_id,
            base_model=base_model,
            dataset_id=dataset_id,
            training_type=training_type,
            config=config,
            status=TrainingStatus.DRAFT,
            device=device,
            precision=precision,
            requested_by=requested_by,
            correlation_id=f"corr_{datetime.utcnow().timestamp()}"
        )
        
        self.training_jobs[job.id] = job
        
        # Audit
        if self.audit_engine:
            self.audit_engine.record(
                actor=requested_by,
                action="TRAINING_JOB_CREATED",
                resource="training_job",
                resource_id=job.id,
                metadata={
                    "model_id": model_id,
                    "dataset_id": dataset_id,
                    "training_type": training_type.value
                }
            )
        
        logger.info(f"Training job created: {job.id} for model {model_id}")
        
        return job
    
    def validate_training_job(self, job_id: str) -> Dict[str, Any]:
        """
        Validate training job before execution.
        
        Checks:
        - Dataset valid
        - Model valid
        - Configuration valid
        - Storage available
        - Device available
        - Memory check
        - Permission check
        - Policy check
        """
        job = self.training_jobs.get(job_id)
        if not job:
            return {"valid": False, "errors": ["Training job not found"]}
        
        errors = []
        warnings = []
        
        # Check dataset
        dataset = self.dataset_registry.get_dataset(job.dataset_id)
        if not dataset:
            errors.append(f"Dataset {job.dataset_id} not found")
        elif dataset.validation_status != DatasetStatus.VALID:
            errors.append(f"Dataset {job.dataset_id} is not valid")
        
        # Check configuration
        if not job.config:
            errors.append("Training configuration is required")
        
        # Check device availability
        # In real implementation, would check actual device availability
        if job.device == "cuda":
            warnings.append("GPU training requires CUDA runtime")
        
        # Update status
        if errors:
            job.status = TrainingStatus.BLOCKED
        else:
            job.status = TrainingStatus.VALIDATING
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def submit_training_job(self, job_id: str, approved_by: Optional[str] = None) -> None:
        """Submit training job for execution."""
        job = self.training_jobs.get(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        # Check if approval is required
        if not approved_by:
            # In real implementation, would check policy
            job.status = TrainingStatus.WAITING_FOR_APPROVAL
            
            if self.approval_engine:
                approval = self.approval_engine.request_approval(
                    mission_id=None,
                    execution_node_id=job.id,
                    requested_by=job.requested_by
                )
                logger.info(f"Training job {job_id} requires approval: {approval.id}")
            
            return
        
        # Job approved
        job.approved_by = approved_by
        job.status = TrainingStatus.QUEUED
        
        logger.info(f"Training job {job_id} submitted and queued")
    
    def start_training(self, job_id: str) -> None:
        """Start training execution."""
        job = self.training_jobs.get(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        if job.status != TrainingStatus.QUEUED:
            raise ValueError(f"Training job must be QUEUED to start (current: {job.status})")
        
        job.status = TrainingStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Audit
        if self.audit_engine:
            self.audit_engine.record(
                actor="system",
                action="TRAINING_STARTED",
                resource="training_job",
                resource_id=job.id,
                metadata={"model_id": job.model_id}
            )
        
        logger.info(f"Training started: {job.id}")
        
        # In real implementation, would start actual training process
        # This is where PyTorch training loop would be executed
    
    def complete_training(
        self,
        job_id: str,
        checkpoint_id: str,
        metrics: Dict[str, Any]
    ) -> None:
        """Complete training job."""
        job = self.training_jobs.get(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        job.status = TrainingStatus.EVALUATING
        job.checkpoint = checkpoint_id
        job.metrics = metrics
        job.completed_at = datetime.utcnow()
        
        logger.info(f"Training completed: {job.id}")
        
        # Audit
        if self.audit_engine:
            self.audit_engine.record(
                actor="system",
                action="TRAINING_COMPLETED",
                resource="training_job",
                resource_id=job.id,
                metadata={"metrics": metrics}
            )
    
    def fail_training(self, job_id: str, error: str) -> None:
        """Mark training job as failed."""
        job = self.training_jobs.get(job_id)
        if not job:
            raise ValueError(f"Training job {job_id} not found")
        
        job.status = TrainingStatus.FAILED
        job.error = error
        job.completed_at = datetime.utcnow()
        
        logger.error(f"Training failed: {job.id} - {error}")
        
        # Audit
        if self.audit_engine:
            self.audit_engine.record(
                actor="system",
                action="TRAINING_FAILED",
                resource="training_job",
                resource_id=job.id,
                status="failure",
                metadata={"error": error}
            )
    
    def create_evaluation_run(
        self,
        model_id: str,
        dataset_id: str,
        checkpoint_id: Optional[str] = None
    ) -> EvaluationRun:
        """Create a new evaluation run."""
        evaluation = EvaluationRun(
            id=f"eval_{datetime.utcnow().timestamp()}",
            model_id=model_id,
            dataset_id=dataset_id,
            checkpoint=checkpoint_id,
            status="PENDING"
        )
        
        self.evaluation_runs[evaluation.id] = evaluation
        
        logger.info(f"Evaluation run created: {evaluation.id} for model {model_id}")
        
        return evaluation
    
    def create_experiment(
        self,
        name: str,
        config: Dict[str, Any],
        dataset_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Experiment:
        """Create a new experiment."""
        experiment = Experiment(
            id=f"exp_{datetime.utcnow().timestamp()}",
            name=name,
            config=config,
            dataset_id=dataset_id,
            model_id=model_id
        )
        
        self.experiments[experiment.id] = experiment
        
        logger.info(f"Experiment created: {experiment.id} ({name})")
        
        return experiment
    
    def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID."""
        return self.training_jobs.get(job_id)
    
    def list_training_jobs(
        self,
        status: Optional[TrainingStatus] = None,
        model_id: Optional[str] = None
    ) -> List[TrainingJob]:
        """List training jobs with optional filters."""
        jobs = list(self.training_jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        if model_id:
            jobs = [j for j in jobs if j.model_id == model_id]
        
        return jobs
