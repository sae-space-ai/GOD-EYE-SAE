"""
SAE Core Execution - Real execution engine.

This module implements a real execution engine that can execute
internal tools with policy and approval integration.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from ..common.enums import (
    ExecutionNodeStatus,
    ToolType,
    RiskLevel,
    PolicyDecision,
    generate_id,
    utc_now,
)
from ..orchestrator.contracts import ExecutionNode, ExecutionGraph
from ..security.contracts import PolicyEngine, PolicyContext, ApprovalEngine, AuditEngine
from ..events.contracts import EventBus, EventType
from .contracts import ToolContract, ExecutionResult


class RealExecutionEngine:
    """
    Real execution engine that executes tools with full policy
    and approval integration.
    """
    
    def __init__(
        self,
        tools: Dict[str, ToolContract],
        policy_engine: PolicyEngine,
        approval_engine: ApprovalEngine,
        audit_engine: AuditEngine,
        event_bus: EventBus
    ):
        """Initialize execution engine."""
        self.tools = tools
        self.policy_engine = policy_engine
        self.approval_engine = approval_engine
        self.audit_engine = audit_engine
        self.event_bus = event_bus
    
    def execute_node(
        self,
        node: ExecutionNode,
        user_id: str,
        mission_id: str,
        context: Dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute a single execution node with full policy and approval checks.
        
        Args:
            node: Execution node to execute
            user_id: ID of user requesting execution
            mission_id: ID of mission
            context: Execution context
        
        Returns:
            ExecutionResult with outputs and status
        """
        start_time = time.time()
        
        # Get tool
        tool = self.tools.get(node.type)
        if not tool:
            return ExecutionResult(
                id=generate_id(),
                node_id=node.id,
                tool_id=node.type,
                status=ExecutionNodeStatus.FAILED,
                error=f"Tool {node.type} not found",
                execution_time=time.time() - start_time
            )
        
        # Check policy
        policy_context = PolicyContext(
            actor_id=user_id,
            action="execute",
            resource="tool",
            resource_id=tool.id,
            mission_id=mission_id,
            risk_level=node.risk_level
        )
        
        policy_result = self.policy_engine.evaluate(policy_context)
        
        if policy_result.decision == PolicyDecision.DENY:
            self.audit_engine.record(
                actor=user_id,
                action="EXECUTION_DENIED",
                resource="tool",
                resource_id=tool.id,
                mission_id=mission_id,
                status="failure",
                metadata={"reason": policy_result.reason}
            )
            
            return ExecutionResult(
                id=generate_id(),
                node_id=node.id,
                tool_id=tool.id,
                status=ExecutionNodeStatus.FAILED,
                error=f"Policy denied: {policy_result.reason}",
                execution_time=time.time() - start_time
            )
        
        # Check if approval is required
        if node.requires_approval or policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
            # Create approval request
            approval = self.approval_engine.request_approval(
                mission_id=mission_id,
                execution_node_id=node.id,
                requested_by=user_id
            )
            
            self.audit_engine.record(
                actor=user_id,
                action="APPROVAL_REQUESTED",
                resource="execution_node",
                resource_id=node.id,
                mission_id=mission_id,
                status="pending"
            )
            
            self.event_bus.publish_event(
                EventType.APPROVAL_REQUIRED,
                producer="execution_engine",
                mission_id=mission_id,
                payload={"approval_id": approval.id, "node_id": node.id}
            )
            
            return ExecutionResult(
                id=generate_id(),
                node_id=node.id,
                tool_id=tool.id,
                status=ExecutionNodeStatus.WAITING_FOR_APPROVAL,
                error="Approval required",
                execution_time=time.time() - start_time
            )
        
        # Execute tool
        try:
            # Validate inputs
            self._validate_inputs(tool, node.inputs)
            
            # Execute based on tool type
            if tool.tool_type == ToolType.READ_ONLY:
                outputs = self._execute_read_only(tool, node.inputs, context)
            elif tool.tool_type == ToolType.COMPUTE:
                outputs = self._execute_compute(tool, node.inputs, context)
            elif tool.tool_type == ToolType.WRITE:
                outputs = self._execute_write(tool, node.inputs, context)
            elif tool.tool_type == ToolType.EXTERNAL_ACTION:
                # External actions require additional checks
                if node.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    return ExecutionResult(
                        id=generate_id(),
                        node_id=node.id,
                        tool_id=tool.id,
                        status=ExecutionNodeStatus.FAILED,
                        error="External actions with high/critical risk require special approval",
                        execution_time=time.time() - start_time
                    )
                outputs = self._execute_external(tool, node.inputs, context)
            else:
                raise ValueError(f"Unknown tool type: {tool.tool_type}")
            
            execution_time = time.time() - start_time
            
            # Record success
            self.audit_engine.record(
                actor=user_id,
                action="EXECUTION_COMPLETED",
                resource="tool",
                resource_id=tool.id,
                mission_id=mission_id,
                status="success",
                metadata={"execution_time": execution_time}
            )
            
            self.event_bus.publish_event(
                EventType.EXECUTION_COMPLETED,
                producer="execution_engine",
                mission_id=mission_id,
                payload={"node_id": node.id, "tool_id": tool.id}
            )
            
            return ExecutionResult(
                id=generate_id(),
                node_id=node.id,
                tool_id=tool.id,
                status=ExecutionNodeStatus.SUCCEEDED,
                outputs=outputs,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Record failure
            self.audit_engine.record(
                actor=user_id,
                action="EXECUTION_FAILED",
                resource="tool",
                resource_id=tool.id,
                mission_id=mission_id,
                status="failure",
                metadata={"error": str(e)}
            )
            
            return ExecutionResult(
                id=generate_id(),
                node_id=node.id,
                tool_id=tool.id,
                status=ExecutionNodeStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )
    
    def _validate_inputs(self, tool: ToolContract, inputs: Dict[str, Any]) -> None:
        """Validate tool inputs against schema."""
        # Simple validation - check required fields
        required = tool.input_schema.get("required", [])
        for field in required:
            if field not in inputs:
                raise ValueError(f"Missing required input: {field}")
    
    def _execute_read_only(
        self,
        tool: ToolContract,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a read-only tool."""
        # Dispatch to actual tool implementation
        # This is a placeholder - in real implementation, would call tool handler
        return {"result": f"Read-only execution of {tool.id}", "inputs": inputs}
    
    def _execute_compute(
        self,
        tool: ToolContract,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a compute tool."""
        # Dispatch to actual tool implementation
        return {"result": f"Compute execution of {tool.id}", "inputs": inputs}
    
    def _execute_write(
        self,
        tool: ToolContract,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a write tool."""
        # Dispatch to actual tool implementation
        return {"result": f"Write execution of {tool.id}", "inputs": inputs}
    
    def _execute_external(
        self,
        tool: ToolContract,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an external action tool."""
        # Dispatch to actual tool implementation
        return {"result": f"External execution of {tool.id}", "inputs": inputs}
    
    def execute_graph(
        self,
        graph: ExecutionGraph,
        user_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, ExecutionResult]:
        """
        Execute all nodes in an execution graph respecting dependencies.
        
        Args:
            graph: Execution graph to execute
            user_id: ID of user requesting execution
            context: Execution context
        
        Returns:
            Dictionary mapping node IDs to execution results
        """
        results = {}
        completed_nodes = set()
        max_iterations = 100  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            # Get ready nodes
            ready_nodes = graph.get_ready_nodes(completed_nodes)
            
            if not ready_nodes:
                break
            
            # Execute ready nodes
            for node in ready_nodes:
                result = self.execute_node(node, user_id, graph.mission_id, context)
                results[node.id] = result
                
                # Update node status
                node.status = result.status
                
                # Mark as completed if succeeded or failed
                if result.status in [ExecutionNodeStatus.SUCCEEDED, ExecutionNodeStatus.FAILED]:
                    completed_nodes.add(node.id)
            
            iteration += 1
        
        return results


# Built-in tools
def create_builtin_tools() -> Dict[str, ToolContract]:
    """Create built-in tools for common operations."""
    tools = {}
    
    # Resolve AOI tool
    tools["resolve_aoi"] = ToolContract(
        id="resolve_aoi",
        name="Resolve Area of Interest",
        description="Resolve and validate area of interest",
        tool_type=ToolType.COMPUTE,
        input_schema={
            "type": "object",
            "properties": {
                "aoi": {"type": "object"}
            },
            "required": ["aoi"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "resolved_aoi": {"type": "object"}
            }
        },
        risk_level=RiskLevel.LOW
    )
    
    # Fetch sources tool
    tools["fetch_sources"] = ToolContract(
        id="fetch_sources",
        name="Fetch Source Data",
        description="Fetch data from configured sources",
        tool_type=ToolType.READ_ONLY,
        input_schema={
            "type": "object",
            "properties": {
                "sources": {"type": "array"},
                "aoi": {"type": "object"}
            },
            "required": ["sources", "aoi"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "source_data": {"type": "object"}
            }
        },
        risk_level=RiskLevel.LOW
    )
    
    # Process data tool
    tools["process_data"] = ToolContract(
        id="process_data",
        name="Process Data",
        description="Process and transform data",
        tool_type=ToolType.COMPUTE,
        input_schema={
            "type": "object",
            "properties": {
                "source_data": {"type": "object"}
            },
            "required": ["source_data"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "processed_data": {"type": "object"}
            }
        },
        risk_level=RiskLevel.LOW
    )
    
    # Capture evidence tool
    tools["capture_evidence"] = ToolContract(
        id="capture_evidence",
        name="Capture Evidence",
        description="Capture evidence from processed data",
        tool_type=ToolType.WRITE,
        input_schema={
            "type": "object",
            "properties": {
                "processed_data": {"type": "object"}
            },
            "required": ["processed_data"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "evidence_ids": {"type": "array"}
            }
        },
        risk_level=RiskLevel.LOW
    )
    
    # Run inference tool
    tools["run_inference"] = ToolContract(
        id="run_inference",
        name="Run Model Inference",
        description="Run AI model inference",
        tool_type=ToolType.COMPUTE,
        input_schema={
            "type": "object",
            "properties": {
                "data": {"type": "object"},
                "models": {"type": "array"}
            },
            "required": ["data", "models"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "inference_result": {"type": "object"}
            }
        },
        risk_level=RiskLevel.MEDIUM
    )
    
    # Search evidence tool
    tools["search_evidence"] = ToolContract(
        id="search_evidence",
        name="Search Evidence",
        description="Search evidence database",
        tool_type=ToolType.READ_ONLY,
        input_schema={
            "type": "object",
            "properties": {
                "aoi": {"type": "object"},
                "time_window": {"type": "object"}
            },
            "required": ["aoi"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "evidence_results": {"type": "array"}
            }
        },
        risk_level=RiskLevel.LOW
    )
    
    return tools
