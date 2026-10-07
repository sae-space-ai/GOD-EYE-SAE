"""
SAE AI Command & Training Center

Central AI management layer for GOD EYE SAE.
Handles model registry, routing, training, evaluation, and governance.
"""

from .models import (
    AICommand,
    AICommandStatus,
    AIIntent,
    ModelCapability,
    AIModel,
    ModelStatus,
    TrainingJob,
    TrainingStatus,
    Dataset,
    DatasetStatus,
    Checkpoint,
    EvaluationRun,
    Experiment,
)

from .command_center import CommandCenter
from .model_registry import ModelRegistry
from .model_router import ModelRouter
from .training_center import TrainingCenter
from .inference_center import InferenceCenter

__all__ = [
    # Models
    "AICommand",
    "AICommandStatus",
    "AIIntent",
    "ModelCapability",
    "AIModel",
    "ModelStatus",
    "TrainingJob",
    "TrainingStatus",
    "Dataset",
    "DatasetStatus",
    "Checkpoint",
    "EvaluationRun",
    "Experiment",
    # Components
    "CommandCenter",
    "ModelRegistry",
    "ModelRouter",
    "TrainingCenter",
    "InferenceCenter",
]
