"""
Base tool class for RCA system.
Provides type validation and standardized execution interface.
"""
from pydantic import BaseModel
from typing import Any, Dict, Optional, TypeVar, Generic

InputT = TypeVar('InputT', bound=BaseModel)
OutputT = TypeVar('OutputT', bound=BaseModel)

class BaseTool(Generic[InputT, OutputT]):
    """
    Base class for all RCA tools with input/output validation.
    Uses Pydantic models for type safety and validation.
    """
    input_model: type[InputT]
    output_model: type[OutputT]
    name: str = "base_tool"
    description: str = "Base tool implementation"
    
    def execute(self, **kwargs) -> OutputT:
        """
        Execute the tool with validated inputs and outputs.
        
        Args:
            **kwargs: Keyword arguments that will be validated against input_model
            
        Returns:
            Validated output model instance
        """
        # Validate inputs
        input_data = self.input_model(**kwargs)
        
        # Execute tool-specific logic
        result = self._execute(input_data)
        
        # Validate and return output
        return self.output_model(**result)
    
    def _execute(self, input_data: InputT) -> Dict[str, Any]:
        """
        Tool-specific execution logic.
        Must be implemented by subclasses.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Dictionary that can be unpacked into output_model
        """
        raise NotImplementedError("Tool must implement _execute method") 