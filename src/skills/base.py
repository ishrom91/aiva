"""
Base classes for the skill system
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession


class BaseSkill(ABC):
    """
    Base class for all skills in Aiva AI Bot.

    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the skill."""
        pass

    def __init__(self) -> None:
        self.skill_id = self.__class__.__name__
        self.skill_name = self.__class__.__name__.replace("Skill", "")

    @abstractmethod
    async def can_handle(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs,
    ) -> bool:
        """
        Determine if this skill can handle the given event.
        This is called for each skill when an event occurs.
        """
        pass

    @abstractmethod
    async def process(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        **kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Process the event and return result.
        Return None if the skill cannot handle the event or processing failed.
        """
        pass

    async def initialize(self, db_session: AsyncSession, master_id: int) -> bool:
        """
        Initialize the skill for a specific master.
        This is called when enabling the skill for a user.
        """
        return True

    async def cleanup(self, db_session: AsyncSession, master_id: int) -> bool:
        """
        Cleanup resources used by the skill for a specific master.
        This is called when disabling the skill for a user.
        """
        return True

    def get_status(self, master_id: int) -> Dict[str, Any]:
        """
        Get current status of the skill for a specific master.
        """
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "enabled": True,
            "master_id": master_id,
        }


class SkillManager:
    """
    Manager class to handle registration and routing of skills.
    """

    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
        self.enabled_skills: Dict[int, list] = {}  # master_id -> list of skill_ids

    def register_skill(self, skill: BaseSkill):
        """Register a skill in the system"""
        self.skills[skill.skill_id] = skill

    def enable_skill_for_master(self, master_id: int, skill_id: str):
        """Enable a skill for a specific master"""
        if master_id not in self.enabled_skills:
            self.enabled_skills[master_id] = []

        if skill_id not in self.enabled_skills[master_id]:
            self.enabled_skills[master_id].append(skill_id)

    def disable_skill_for_master(self, master_id: int, skill_id: str):
        """Disable a skill for a specific master"""
        if (
            master_id in self.enabled_skills
            and skill_id in self.enabled_skills[master_id]
        ):
            self.enabled_skills[master_id].remove(skill_id)

    async def route_event(
        self,
        message: Union[Message, CallbackQuery],
        state: FSMContext,
        db_session: AsyncSession,
        master_id: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Route an event to the appropriate skill based on the master's enabled skills
        """
        # Get enabled skills for this master
        enabled_skill_ids = self.enabled_skills.get(master_id, [])

        # Try each enabled skill to see if it can handle the event
        for skill_id in enabled_skill_ids:
            if skill_id in self.skills:
                skill = self.skills[skill_id]
                try:
                    if await skill.can_handle(message, state, db_session):
                        return await skill.process(message, state, db_session)
                except Exception as e:
                    # Log the error but continue trying other skills
                    print(f"Error processing skill {skill_id}: {e}")
                    continue

        # No skill handled the event
        return None
