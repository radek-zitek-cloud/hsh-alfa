"""AI Tools API routes."""

import logging
from typing import List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_auth
from app.services.database import get_db
from app.models.ai_tool import (
    AIToolApply,
    AIToolCreate,
    AIToolResponse,
    AIToolUpdate,
)
from app.models.note import NoteCreate
from app.services.ai_tool_service import AIToolService
from app.services.note_service import NoteService

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


@router.get("/", response_model=List[AIToolResponse])
@limiter.limit("100/minute")
async def list_tools(
    request: Request,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List all AI tools for the current user."""
    service = AIToolService(db)
    tools = await service.list_tools(user_id)
    return tools


@router.get("/{tool_id}", response_model=AIToolResponse)
@limiter.limit("100/minute")
async def get_tool(
    request: Request,
    tool_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific AI tool."""
    service = AIToolService(db)
    tool = await service.get_tool(tool_id, user_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


@router.post("/", response_model=AIToolResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_tool(
    request: Request,
    tool_data: AIToolCreate,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI tool."""
    service = AIToolService(db)
    tool = await service.create_tool(tool_data, user_id)
    logger.info(f"User {user_id} created AI tool {tool.id}")
    return tool


@router.put("/{tool_id}", response_model=AIToolResponse)
@limiter.limit("20/minute")
async def update_tool(
    request: Request,
    tool_id: int,
    tool_data: AIToolUpdate,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update an AI tool."""
    service = AIToolService(db)
    tool = await service.update_tool(tool_id, tool_data, user_id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    logger.info(f"User {user_id} updated AI tool {tool_id}")
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_tool(
    request: Request,
    tool_id: int,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete an AI tool."""
    service = AIToolService(db)
    success = await service.delete_tool(tool_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    logger.info(f"User {user_id} deleted AI tool {tool_id}")
    return None


@router.post("/apply", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def apply_tool(
    request: Request,
    apply_data: AIToolApply,
    user_id: int = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Apply an AI tool to a note and create a subnote with the result."""
    tool_service = AIToolService(db)
    note_service = NoteService(db)

    # Get the note
    note = await note_service.get_note(apply_data.note_id, user_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    # Get the tool
    tool = await tool_service.get_tool(apply_data.tool_id, user_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found"
        )

    # Prepare the prompt by replacing placeholder
    note_content = f"Title: {note.title}\n\nContent: {note.content or ''}"
    prompt = tool.prompt.replace("[PLACEHOLDER]", note_content)

    # Call OpenAI API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {tool.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI API error: {e.response.status_code}",
        )
    except httpx.TimeoutException:
        logger.error("OpenAI API timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="AI API timeout"
        )
    except Exception as e:
        logger.error(f"Unexpected error calling AI API: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process AI request",
        )

    # Count existing subnotes to determine position
    all_notes = await note_service.list_notes(user_id)
    subnotes = [n for n in all_notes if n.parent_id == apply_data.note_id]
    next_position = len(subnotes)

    # Create a new subnote with the AI response
    subnote_data = NoteCreate(
        title=f"AI Analysis: {tool.name}",
        content=ai_response,
        parent_id=apply_data.note_id,
        position=next_position,
    )
    subnote = await note_service.create_note(subnote_data, user_id)

    logger.info(
        f"User {user_id} applied tool {tool.id} to note {note.id}, created subnote {subnote.id}"
    )

    return {
        "message": "Tool applied successfully",
        "subnote_id": subnote.id,
        "tool_name": tool.name,
    }
