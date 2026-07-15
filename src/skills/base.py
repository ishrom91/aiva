from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class PermissionLevel(Enum):
    """Permission levels for skills"""
    PUBLIC = "public"      # Available to all users
    REGISTERED = "registered"  # Available to registered users
    PREMIUM = "premium"    # Available to premium users
    ADMIN = "admin"        # Admin-only features


class BaseSkill(ABC):
    """
    Abstract base class for all skills in the Aiva AI system.
    Skills are modular capabilities that the AI agent can perform.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def can_handle(self, event: Dict[str, Any]) -> bool:
        """
        Determine if this skill can handle the given event.
        
        Args:
            event: Dictionary containing event data (message, callback, etc.)
            
        Returns:
            bool: True if skill can handle the event, False otherwise
        """
        pass
    
    @abstractmethod
    async def handle(self, event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle the event and return response.
        
        Args:
            event: Dictionary containing event data
            context: Contextual information (user data, session state, etc.)
            
        Returns:
            Dict: Response data to send back to user
        """
        pass
    
    def get_required_permissions(self) -> List[PermissionLevel]:
        """
        Get the permission levels required to use this skill.
        
        Returns:
            List[PermissionLevel]: List of required permission levels
        """
        return [PermissionLevel.PUBLIC]
    
    def get_supported_commands(self) -> List[str]:
        """
        Get list of commands supported by this skill.
        
        Returns:
            List[str]: List of supported commands
        """
        return []
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data for the skill.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        return True
    
    async def preprocess(self, event: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preprocess the event before handling.
        
        Args:
            event: Event data
            context: Context data
            
        Returns:
            Dict: Processed event data
        """
        return event
    
    async def postprocess(self, response: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Postprocess the response after handling.
        
        Args:
            response: Raw response from handle method
            context: Context data
            
        Returns:
            Dict: Processed response
        """
        return response