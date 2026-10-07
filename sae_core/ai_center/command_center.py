"""
SAE AI Command Center

Handles natural language commands, intent parsing, validation, and execution routing.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import logging

from .models import (
    AICommand, AICommandStatus, AIIntent, AIRequest,
    ModelCapability, ModelSelection
)

logger = logging.getLogger(__name__)


class IntentParser:
    """Parses natural language commands into structured intents."""
    
    # Intent patterns (simple keyword-based for now)
    INTENT_PATTERNS = {
        AIIntent.EXPLORE_AREA: [r"explorar?\s+(zona|área|región|territorio)", r"analizar\s+(zona|área)"],
        AIIntent.ANALYZE_CHANGE: [r"cambios?\s+entre", r"comparar\s+(fechas|imágenes|periodos)"],
        AIIntent.ASSESS_RISK: [r"riesgo\s+de\s+incendio", r"evaluar\s+riesgo", r"analizar\s+riesgo"],
        AIIntent.SEARCH_EVIDENCE: [r"buscar\s+evidencia", r"evidencias?\s+de"],
        AIIntent.COMPARE_DATA: [r"comparar\s+(imágenes|datos|sar|lidar)"],
        AIIntent.RUN_INFERENCE: [r"ejecutar\s+inferencia", r"analizar\s+(sar|lidar|imagen)"],
        AIIntent.PREDICT_EVENT: [r"predecir", r"pronóstico", r"predicción"],
        AIIntent.PLAN_ACQUISITION: [r"planificar\s+adquisición", r"plan\s+de\s+adquisición"],
        AIIntent.CREATE_MISSION: [r"crear\s+misión", r"nueva\s+misión"],
        AIIntent.TRAIN_MODEL: [r"entrenar\s+(modelo|red)", r"training"],
        AIIntent.FINE_TUNE_MODEL: [r"fine.?tun", r"ajustar\s+modelo"],
        AIIntent.EVALUATE_MODEL: [r"evaluar\s+(modelo|red)", r"evaluación"],
        AIIntent.COMPARE_MODELS: [r"comparar\s+modelos"],
        AIIntent.DEPLOY_MODEL: [r"desplegar\s+modelo", r"deploy"],
        AIIntent.DISABLE_MODEL: [r"desactivar\s+modelo", r"disable"],
        AIIntent.CREATE_CAMPAIGN: [r"crear\s+campaña", r"nueva\s+campaña"],
        AIIntent.OPTIMIZE_PROMOTION: [r"optimizar\s+(campaña|promoción|ranking)"],
        AIIntent.GENERATE_REPORT: [r"generar\s+reporte", r"crear\s+informe"],
        AIIntent.EXPORT_RESULT: [r"exportar\s+(resultado|datos)"],
    }
    
    def parse(self, command: str) -> AIIntent:
        """Parse command text into intent."""
        command_lower = command.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, command_lower):
                    logger.info(f"Parsed intent: {intent.value} from command: {command[:50]}...")
                    return intent
        
        logger.warning(f"Unknown intent for command: {command[:50]}...")
        return AIIntent.UNKNOWN


class CommandValidator:
    """Validates AI commands against schema and policies."""
    
    def __init__(self, model_registry, policy_engine):
        self.model_registry = model_registry
        self.policy_engine = policy_engine
    
    def validate(self, command: AICommand) -> Dict[str, Any]:
        """
        Validate command.
        
        Returns:
            Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
        """
        errors = []
        warnings = []
        
        # Check intent is known
        if command.intent == AIIntent.UNKNOWN:
            errors.append("Unknown intent cannot be executed automatically")
        
        # Check required parameters based on intent
        required_params = self._get_required_params(command.intent)
        for param in required_params:
            if param not in command.parameters:
                errors.append(f"Missing required parameter: {param}")
        
        # Check model availability if inference is requested
        if command.intent in [AIIntent.RUN_INFERENCE, AIIntent.TRAIN_MODEL]:
            if not command.requested_capabilities:
                warnings.append("No capabilities specified, model selection may be suboptimal")
        
        # Check permissions
        # (In real implementation, would check against user permissions)
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings
        }
    
    def _get_required_params(self, intent: AIIntent) -> List[str]:
        """Get required parameters for intent."""
        requirements = {
            AIIntent.EXPLORE_AREA: ["area_of_interest"],
            AIIntent.ANALYZE_CHANGE: ["area_of_interest", "time_range"],
            AIIntent.ASSESS_RISK: ["area_of_interest", "risk_type"],
            AIIntent.RUN_INFERENCE: ["input_data"],
            AIIntent.TRAIN_MODEL: ["model_id", "dataset_id"],
            AIIntent.EVALUATE_MODEL: ["model_id", "dataset_id"],
            AIIntent.CREATE_CAMPAIGN: ["name", "objective"],
        }
        return requirements.get(intent, [])


class CommandRouter:
    """Routes commands to appropriate models and tools."""
    
    def __init__(self, model_router, tool_registry):
        self.model_router = model_router
        self.tool_registry = tool_registry
    
    def route(self, command: AICommand) -> Dict[str, Any]:
        """
        Route command to model and tools.
        
        Returns:
            Dict with 'model_selection', 'tools', 'requires_approval'
        """
        # Build AI request from command
        request = AIRequest(
            id=command.id,
            mission_id=command.mission_id,
            intent=command.intent,
            required_capabilities=[ModelCapability(c) for c in command.requested_capabilities],
            risk_level=command.risk_level,
            context=command.parameters
        )
        
        # Select model
        model_selection = self.model_router.select_model(request)
        
        # Determine required tools
        tools = self._get_required_tools(command.intent)
        
        # Check if approval is required
        requires_approval = self._check_approval_required(command, model_selection)
        
        return {
            "model_selection": model_selection,
            "tools": tools,
            "requires_approval": requires_approval
        }
    
    def _get_required_tools(self, intent: AIIntent) -> List[str]:
        """Get required tools for intent."""
        tool_mapping = {
            AIIntent.EXPLORE_AREA: ["fetch_sources", "process_data"],
            AIIntent.ANALYZE_CHANGE: ["fetch_timeseries", "run_inference"],
            AIIntent.ASSESS_RISK: ["fetch_sources", "run_inference"],
            AIIntent.RUN_INFERENCE: ["run_inference"],
            AIIntent.TRAIN_MODEL: ["train_model"],
            AIIntent.EVALUATE_MODEL: ["evaluate_model"],
        }
        return tool_mapping.get(intent, [])
    
    def _check_approval_required(self, command: AICommand, model_selection: ModelSelection) -> bool:
        """Check if command requires approval."""
        # High risk commands require approval
        if command.risk_level in ["HIGH", "CRITICAL"]:
            return True
        
        # Training jobs require approval
        if command.intent in [AIIntent.TRAIN_MODEL, AIIntent.FINE_TUNE_MODEL]:
            return True
        
        # Model deployment requires approval
        if command.intent == AIIntent.DEPLOY_MODEL:
            return True
        
        return False


class CommandCenter:
    """
    Main command center for AI operations.
    
    Orchestrates command parsing, validation, routing, and execution.
    """
    
    def __init__(
        self,
        model_registry,
        model_router,
        policy_engine,
        approval_engine,
        audit_engine,
        tool_registry
    ):
        self.model_registry = model_registry
        self.model_router = model_router
        self.policy_engine = policy_engine
        self.approval_engine = approval_engine
        self.audit_engine = audit_engine
        self.tool_registry = tool_registry
        
        self.intent_parser = IntentParser()
        self.command_validator = CommandValidator(model_registry, policy_engine)
        self.command_router = CommandRouter(model_router, tool_registry)
        
        self.commands: Dict[str, AICommand] = {}
    
    def submit_command(
        self,
        raw_command: str,
        actor: str,
        mission_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        risk_level: str = "LOW"
    ) -> AICommand:
        """
        Submit a new command.
        
        Args:
            raw_command: Natural language command
            actor: User ID
            mission_id: Optional mission ID
            parameters: Optional structured parameters
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
        
        Returns:
            AICommand with current status
        """
        # Parse intent
        intent = self.intent_parser.parse(raw_command)
        
        # Create command
        command = AICommand(
            id=f"cmd_{datetime.utcnow().timestamp()}",
            actor=actor,
            raw_command=raw_command,
            intent=intent,
            mission_id=mission_id,
            parameters=parameters or {},
            risk_level=risk_level,
            status=AICommandStatus.RECEIVED,
            correlation_id=f"corr_{datetime.utcnow().timestamp()}"
        )
        
        self.commands[command.id] = command
        
        # Audit
        self.audit_engine.record(
            actor=actor,
            action="COMMAND_RECEIVED",
            resource="ai_command",
            resource_id=command.id,
            mission_id=mission_id,
            metadata={"intent": intent.value, "risk_level": risk_level}
        )
        
        logger.info(f"Command submitted: {command.id} with intent {intent.value}")
        
        return command
    
    def validate_command(self, command_id: str) -> Dict[str, Any]:
        """Validate a command."""
        command = self.commands.get(command_id)
        if not command:
            return {"valid": False, "errors": ["Command not found"]}
        
        validation = self.command_validator.validate(command)
        
        if validation["valid"]:
            command.status = AICommandStatus.VALIDATED
        else:
            command.status = AICommandStatus.REJECTED
            command.error = "; ".join(validation["errors"])
        
        return validation
    
    def route_command(self, command_id: str) -> Dict[str, Any]:
        """Route command to model and tools."""
        command = self.commands.get(command_id)
        if not command:
            return {"error": "Command not found"}
        
        if command.status != AICommandStatus.VALIDATED:
            return {"error": f"Command must be validated first (current status: {command.status})"}
        
        routing = self.command_router.route(command)
        
        if routing["requires_approval"]:
            command.status = AICommandStatus.WAITING_FOR_APPROVAL
            
            # Create approval request
            approval = self.approval_engine.request_approval(
                mission_id=command.mission_id,
                execution_node_id=command.id,
                requested_by=command.actor
            )
            
            logger.info(f"Command {command_id} requires approval: {approval.id}")
        
        return routing
    
    def execute_command(self, command_id: str) -> Dict[str, Any]:
        """
        Execute a command.
        
        In real implementation, this would:
        1. Call the selected model
        2. Execute required tools
        3. Capture evidence
        4. Record audit trail
        5. Return results
        """
        command = self.commands.get(command_id)
        if not command:
            return {"error": "Command not found"}
        
        if command.status not in [AICommandStatus.VALIDATED, AICommandStatus.READY]:
            return {"error": f"Command not ready for execution (status: {command.status})"}
        
        command.status = AICommandStatus.RUNNING
        
        # Audit
        self.audit_engine.record(
            actor=command.actor,
            action="COMMAND_EXECUTION_STARTED",
            resource="ai_command",
            resource_id=command.id,
            mission_id=command.mission_id
        )
        
        try:
            # In real implementation, would execute model/tools here
            # For now, simulate execution
            result = {
                "status": "success",
                "message": f"Command {command.intent.value} executed successfully",
                "data": {}
            }
            
            command.status = AICommandStatus.COMPLETED
            command.result = result
            
            logger.info(f"Command {command_id} completed successfully")
            
        except Exception as e:
            command.status = AICommandStatus.FAILED
            command.error = str(e)
            
            logger.error(f"Command {command_id} failed: {e}")
            
            # Audit failure
            self.audit_engine.record(
                actor=command.actor,
                action="COMMAND_EXECUTION_FAILED",
                resource="ai_command",
                resource_id=command.id,
                mission_id=command.mission_id,
                status="failure",
                metadata={"error": str(e)}
            )
            
            raise
        
        return result
    
    def get_command(self, command_id: str) -> Optional[AICommand]:
        """Get command by ID."""
        return self.commands.get(command_id)
    
    def list_commands(self, actor: Optional[str] = None) -> List[AICommand]:
        """List commands, optionally filtered by actor."""
        if actor:
            return [cmd for cmd in self.commands.values() if cmd.actor == actor]
        return list(self.commands.values())
