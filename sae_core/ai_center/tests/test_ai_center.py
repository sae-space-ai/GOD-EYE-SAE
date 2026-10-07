"""
Tests for SAE AI Command & Training Center.
"""

import pytest
from datetime import datetime

from sae_core.ai_center.models import (
    AICommand, AICommandStatus, AIIntent, AIModel, ModelStatus,
    ModelCapability, ModelType, TrainingJob, TrainingStatus,
    Dataset, DatasetStatus, Checkpoint, EvaluationRun
)
from sae_core.ai_center.command_center import CommandCenter, IntentParser, CommandValidator, CommandRouter
from sae_core.ai_center.model_registry import ModelRegistry
from sae_core.ai_center.model_router import ModelRouter
from sae_core.ai_center.training_center import TrainingCenter, DatasetRegistry, CheckpointManager
from sae_core.ai_center.inference_center import InferenceCenter, InferenceRequest


# ============================================================================
# INTENT PARSER TESTS
# ============================================================================

class TestIntentParser:
    """Test intent parsing from natural language."""
    
    def test_parse_explore_area(self):
        """Test parsing explore area intent."""
        parser = IntentParser()
        
        intent = parser.parse("Explorar la zona")
        assert intent == AIIntent.EXPLORE_AREA
        
        intent = parser.parse("Analizar área de interés")
        assert intent == AIIntent.EXPLORE_AREA
    
    def test_parse_analyze_change(self):
        """Test parsing analyze change intent."""
        parser = IntentParser()
        
        intent = parser.parse("Buscar cambios entre fechas")
        assert intent == AIIntent.ANALYZE_CHANGE
        
        intent = parser.parse("Comparar imágenes")
        assert intent == AIIntent.COMPARE_DATA
    
    def test_parse_assess_risk(self):
        """Test parsing assess risk intent."""
        parser = IntentParser()
        
        intent = parser.parse("Analiza riesgo de incendio")
        assert intent == AIIntent.ASSESS_RISK
        
        intent = parser.parse("Evaluar riesgo")
        assert intent == AIIntent.ASSESS_RISK
    
    def test_parse_train_model(self):
        """Test parsing train model intent."""
        parser = IntentParser()
        
        intent = parser.parse("Entrenar modelo")
        assert intent == AIIntent.TRAIN_MODEL
        
        intent = parser.parse("Fine-tune del modelo")
        assert intent == AIIntent.FINE_TUNE_MODEL
    
    def test_parse_unknown(self):
        """Test parsing unknown intent."""
        parser = IntentParser()
        
        intent = parser.parse("Algo completamente diferente")
        assert intent == AIIntent.UNKNOWN


# ============================================================================
# MODEL REGISTRY TESTS
# ============================================================================

class TestModelRegistry:
    """Test model registry operations."""
    
    def test_register_model(self):
        """Test model registration."""
        registry = ModelRegistry()
        
        model = AIModel(
            id="test-model-1",
            name="Test Model",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"]
        )
        
        registry.register_model(model)
        
        retrieved = registry.get_model("test-model-1")
        assert retrieved is not None
        assert retrieved.id == "test-model-1"
        assert retrieved.name == "Test Model"
    
    def test_register_duplicate_model(self):
        """Test registering duplicate model raises error."""
        registry = ModelRegistry()
        
        model = AIModel(
            id="test-model-1",
            name="Test Model",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"]
        )
        
        registry.register_model(model)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register_model(model)
    
    def test_update_model_status(self):
        """Test updating model status."""
        registry = ModelRegistry()
        
        model = AIModel(
            id="test-model-1",
            name="Test Model",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"],
            status=ModelStatus.REGISTERED
        )
        
        registry.register_model(model)
        registry.update_model_status("test-model-1", ModelStatus.READY)
        
        retrieved = registry.get_model("test-model-1")
        assert retrieved.status == ModelStatus.READY
    
    def test_list_models_by_capability(self):
        """Test listing models by capability."""
        registry = ModelRegistry()
        
        model1 = AIModel(
            id="model-1",
            name="Model 1",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"],
            status=ModelStatus.READY
        )
        
        model2 = AIModel(
            id="model-2",
            name="Model 2",
            provider="test",
            version="1.0",
            model_type=ModelType.CLASSIFIER,
            capabilities=[ModelCapability.CLASSIFICATION],
            modalities=["text"],
            status=ModelStatus.READY
        )
        
        registry.register_model(model1)
        registry.register_model(model2)
        
        text_models = registry.get_models_by_capability(ModelCapability.TEXT_GENERATION)
        assert len(text_models) == 1
        assert text_models[0].id == "model-1"
    
    def test_validate_model(self):
        """Test model validation."""
        registry = ModelRegistry()
        
        model = AIModel(
            id="test-model-1",
            name="Test Model",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"]
        )
        
        registry.register_model(model)
        
        validation = registry.validate_model("test-model-1")
        assert validation["valid"] is True


# ============================================================================
# COMMAND CENTER TESTS
# ============================================================================

class TestCommandCenter:
    """Test command center operations."""
    
    def test_submit_command(self):
        """Test submitting a command."""
        model_registry = ModelRegistry()
        model_router = ModelRouter(model_registry)
        
        # Mock dependencies
        class MockPolicyEngine:
            def evaluate(self, *args, **kwargs):
                return {"allowed": True}
        
        class MockApprovalEngine:
            def request_approval(self, *args, **kwargs):
                return {"id": "approval-1"}
        
        class MockAuditEngine:
            def record(self, *args, **kwargs):
                pass
        
        command_center = CommandCenter(
            model_registry=model_registry,
            model_router=model_router,
            policy_engine=MockPolicyEngine(),
            approval_engine=MockApprovalEngine(),
            audit_engine=MockAuditEngine(),
            tool_registry={}
        )
        
        command = command_center.submit_command(
            raw_command="Analiza riesgo de incendio",
            actor="user-1",
            risk_level="MEDIUM"
        )
        
        assert command.id is not None
        assert command.intent == AIIntent.ASSESS_RISK
        assert command.status == AICommandStatus.RECEIVED
        assert command.actor == "user-1"
    
    def test_validate_command(self):
        """Test command validation."""
        model_registry = ModelRegistry()
        model_router = ModelRouter(model_registry)
        
        class MockPolicyEngine:
            def evaluate(self, *args, **kwargs):
                return {"allowed": True}
        
        class MockApprovalEngine:
            def request_approval(self, *args, **kwargs):
                return {"id": "approval-1"}
        
        class MockAuditEngine:
            def record(self, *args, **kwargs):
                pass
        
        command_center = CommandCenter(
            model_registry=model_registry,
            model_router=model_router,
            policy_engine=MockPolicyEngine(),
            approval_engine=MockApprovalEngine(),
            audit_engine=MockAuditEngine(),
            tool_registry={}
        )
        
        command = command_center.submit_command(
            raw_command="Analiza riesgo de incendio",
            actor="user-1",
            parameters={"area_of_interest": {"lat": 0, "lng": 0}},
            risk_level="MEDIUM"
        )
        
        validation = command_center.validate_command(command.id)
        assert validation["valid"] is True
        assert command.status == AICommandStatus.VALIDATED


# ============================================================================
# MODEL ROUTER TESTS
# ============================================================================

class TestModelRouter:
    """Test model routing."""
    
    def test_select_model(self):
        """Test model selection."""
        registry = ModelRegistry()
        
        model = AIModel(
            id="test-model-1",
            name="Test Model",
            provider="test",
            version="1.0",
            model_type=ModelType.LLM,
            capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
            modalities=["text"],
            status=ModelStatus.READY
        )
        
        registry.register_model(model)
        
        router = ModelRouter(registry)
        
        from sae_core.ai_center.models import AIRequest
        
        request = AIRequest(
            id="req-1",
            required_capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"]
        )
        
        selection = router.select_model(request)
        
        assert selection.selected_model.id == "test-model-1"
        assert len(selection.alternatives) == 0
    
    def test_select_model_no_candidates(self):
        """Test model selection with no candidates."""
        registry = ModelRegistry()
        router = ModelRouter(registry)
        
        from sae_core.ai_center.models import AIRequest, ModelCapability
        
        request = AIRequest(
            id="req-1",
            required_capabilities=[ModelCapability.TEXT_GENERATION],
            modalities=["text"]
        )
        
        with pytest.raises(ValueError, match="No models available"):
            router.select_model(request)


# ============================================================================
# TRAINING CENTER TESTS
# ============================================================================

class TestTrainingCenter:
    """Test training center operations."""
    
    def test_create_training_job(self):
        """Test creating a training job."""
        dataset_registry = DatasetRegistry()
        checkpoint_manager = CheckpointManager()
        
        # Register a valid dataset
        dataset = Dataset(
            id="dataset-1",
            name="Test Dataset",
            version="1.0",
            modality="text",
            location="/data/test",
            format="json",
            validation_status=DatasetStatus.VALID
        )
        dataset_registry.register_dataset(dataset)
        
        training_center = TrainingCenter(
            dataset_registry=dataset_registry,
            checkpoint_manager=checkpoint_manager
        )
        
        job = training_center.create_training_job(
            model_id="model-1",
            base_model="base-model-1",
            dataset_id="dataset-1",
            training_type="FINE_TUNING",
            config={"epochs": 10, "batch_size": 32},
            requested_by="user-1"
        )
        
        assert job.id is not None
        assert job.model_id == "model-1"
        assert job.dataset_id == "dataset-1"
        assert job.status == TrainingStatus.DRAFT
    
    def test_create_training_job_invalid_dataset(self):
        """Test creating training job with invalid dataset."""
        dataset_registry = DatasetRegistry()
        checkpoint_manager = CheckpointManager()
        
        # Register an invalid dataset
        dataset = Dataset(
            id="dataset-1",
            name="Test Dataset",
            version="1.0",
            modality="text",
            location="/data/test",
            format="json",
            validation_status=DatasetStatus.INVALID
        )
        dataset_registry.register_dataset(dataset)
        
        training_center = TrainingCenter(
            dataset_registry=dataset_registry,
            checkpoint_manager=checkpoint_manager
        )
        
        with pytest.raises(ValueError, match="not valid"):
            training_center.create_training_job(
                model_id="model-1",
                base_model="base-model-1",
                dataset_id="dataset-1",
                training_type="FINE_TUNING",
                config={"epochs": 10},
                requested_by="user-1"
            )


# ============================================================================
# INFERENCE CENTER TESTS
# ============================================================================

class TestInferenceCenter:
    """Test inference center operations."""
    
    def test_inference_request(self):
        """Test inference request creation."""
        request = InferenceRequest(
            id="req-1",
            model_id="model-1",
            inputs={"text": "Hello world"},
            parameters={"temperature": 0.7}
        )
        
        assert request.id == "req-1"
        assert request.model_id == "model-1"
        assert request.inputs["text"] == "Hello world"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
