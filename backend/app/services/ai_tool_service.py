"""Service layer for AI Tool operations."""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_tool import AITool, AIToolCreate, AIToolUpdate

logger = logging.getLogger(__name__)


class AIToolService:
    """Service for managing AI tools."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def list_tools(self, user_id: int) -> List[AITool]:
        """List all AI tools for a user."""
        result = await self.db.execute(
            select(AITool)
            .where(AITool.user_id == user_id)
            .order_by(AITool.created.desc())
        )
        tools = result.scalars().all()
        logger.info(f"Listed {len(tools)} AI tools for user {user_id}")
        return tools

    async def get_tool(self, tool_id: int, user_id: int) -> Optional[AITool]:
        """Get a specific AI tool."""
        result = await self.db.execute(
            select(AITool).where(AITool.id == tool_id, AITool.user_id == user_id)
        )
        tool = result.scalar_one_or_none()
        if tool:
            logger.info(f"Retrieved AI tool {tool_id} for user {user_id}")
        else:
            logger.warning(f"AI tool {tool_id} not found for user {user_id}")
        return tool

    async def create_tool(self, tool_data: AIToolCreate, user_id: int) -> AITool:
        """Create a new AI tool."""
        tool = AITool(
            user_id=user_id,
            name=tool_data.name,
            description=tool_data.description,
            prompt=tool_data.prompt,
            api_key=tool_data.api_key,
        )
        self.db.add(tool)
        await self.db.commit()
        await self.db.refresh(tool)
        logger.info(f"Created AI tool {tool.id} for user {user_id}")
        return tool

    async def update_tool(
        self, tool_id: int, tool_data: AIToolUpdate, user_id: int
    ) -> Optional[AITool]:
        """Update an AI tool."""
        tool = await self.get_tool(tool_id, user_id)
        if not tool:
            return None

        if tool_data.name is not None:
            tool.name = tool_data.name
        if tool_data.description is not None:
            tool.description = tool_data.description
        if tool_data.prompt is not None:
            tool.prompt = tool_data.prompt
        if tool_data.api_key is not None:
            tool.api_key = tool_data.api_key

        await self.db.commit()
        await self.db.refresh(tool)
        logger.info(f"Updated AI tool {tool_id} for user {user_id}")
        return tool

    async def delete_tool(self, tool_id: int, user_id: int) -> bool:
        """Delete an AI tool."""
        tool = await self.get_tool(tool_id, user_id)
        if not tool:
            return False

        await self.db.delete(tool)
        await self.db.commit()
        logger.info(f"Deleted AI tool {tool_id} for user {user_id}")
        return True
