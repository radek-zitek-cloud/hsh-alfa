"""AI Tools API routes."""

import logging
from datetime import datetime
from typing import List

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
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
from app.models.note import NoteCreate, NoteUpdate
from app.models.user import User
from app.services.ai_tool_service import AIToolService
from app.services.note_service import NoteService

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/ai-tools", tags=["ai-tools"])


async def process_ai_tool_async(
    subnote_id: int,
    prompt: str,
    api_key: str,
    tool_name: str,
    user_id: int,
    model: str = "claude-sonnet-4-5-20250929",
):
    """Background task to process AI tool application asynchronously."""
    from app.services.database import get_async_session

    try:
        # Call Anthropic API
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for long processing
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            result = response.json()
            ai_response = result["content"][0]["text"]

        # Update subnote with the result
        async with get_async_session() as db:
            try:
                note_service = NoteService(db)
                update_data = NoteUpdate(content=ai_response)
                await note_service.update_note(subnote_id, update_data, user_id)
                await db.commit()
                logger.info(f"Successfully processed AI tool for subnote {subnote_id}")
            except Exception as e:
                await db.rollback()
                logger.error(f"Error updating subnote {subnote_id}: {str(e)}")
                raise

    except httpx.HTTPStatusError as e:
        logger.error(f"Anthropic API error for subnote {subnote_id}: {e.response.status_code} - {e.response.text}")
        error_message = f"**Error:** AI API returned status code {e.response.status_code}\n\nPlease try again later."
        async with get_async_session() as db:
            try:
                note_service = NoteService(db)
                update_data = NoteUpdate(content=error_message)
                await note_service.update_note(subnote_id, update_data, user_id)
                await db.commit()
            except Exception as update_error:
                await db.rollback()
                logger.error(f"Error updating subnote {subnote_id} with error message: {str(update_error)}")

    except httpx.TimeoutException:
        logger.error(f"Anthropic API timeout for subnote {subnote_id}")
        error_message = "**Error:** AI processing timed out\n\nPlease try again later."
        async with get_async_session() as db:
            try:
                note_service = NoteService(db)
                update_data = NoteUpdate(content=error_message)
                await note_service.update_note(subnote_id, update_data, user_id)
                await db.commit()
            except Exception as update_error:
                await db.rollback()
                logger.error(f"Error updating subnote {subnote_id} with timeout message: {str(update_error)}")

    except Exception as e:
        logger.error(f"Unexpected error processing AI tool for subnote {subnote_id}: {str(e)}")
        error_message = f"**Error:** Failed to process AI request\n\n{str(e)}\n\nPlease try again later."
        async with get_async_session() as db:
            try:
                note_service = NoteService(db)
                update_data = NoteUpdate(content=error_message)
                await note_service.update_note(subnote_id, update_data, user_id)
                await db.commit()
            except Exception as update_error:
                await db.rollback()
                logger.error(f"Error updating subnote {subnote_id} with error message: {str(update_error)}")


@router.get("/", response_model=List[AIToolResponse])
@limiter.limit("100/minute")
async def list_tools(
    request: Request,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """List all AI tools for the current user."""
    service = AIToolService(db)
    tools = await service.list_tools(current_user.id)
    return tools


@router.get("/{tool_id}", response_model=AIToolResponse)
@limiter.limit("100/minute")
async def get_tool(
    request: Request,
    tool_id: int,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific AI tool."""
    service = AIToolService(db)
    tool = await service.get_tool(tool_id, current_user.id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    return tool


@router.post("/", response_model=AIToolResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_tool(
    request: Request,
    tool_data: AIToolCreate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI tool."""
    service = AIToolService(db)
    tool = await service.create_tool(tool_data, current_user.id)
    logger.info(f"User {current_user.id} created AI tool {tool.id}")
    return tool


@router.put("/{tool_id}", response_model=AIToolResponse)
@limiter.limit("20/minute")
async def update_tool(
    request: Request,
    tool_id: int,
    tool_data: AIToolUpdate,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Update an AI tool."""
    service = AIToolService(db)
    tool = await service.update_tool(tool_id, tool_data, current_user.id)
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    logger.info(f"User {current_user.id} updated AI tool {tool_id}")
    return tool


@router.delete("/{tool_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_tool(
    request: Request,
    tool_id: int,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Delete an AI tool."""
    service = AIToolService(db)
    success = await service.delete_tool(tool_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")
    logger.info(f"User {current_user.id} deleted AI tool {tool_id}")
    return None


@router.post("/apply", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def apply_tool(
    request: Request,
    apply_data: AIToolApply,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Apply an AI tool to a note and create a subnote with the result asynchronously."""
    tool_service = AIToolService(db)
    note_service = NoteService(db)

    # Get the note
    note = await note_service.get_note(apply_data.note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
        )

    # Get the tool
    tool = await tool_service.get_tool(apply_data.tool_id, current_user.id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found"
        )

    # Count existing subnotes to determine position
    all_notes = await note_service.list_notes(current_user.id)
    subnotes = [n for n in all_notes if n.parent_id == apply_data.note_id]
    next_position = len(subnotes)

    # Create timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Create placeholder content with timestamp and status
    placeholder_content = f"""**AI Processing Status**

**Tool:** {tool.name}
**Started:** {timestamp}
**Status:** Processing...

The AI is analyzing your note. This may take a few minutes. Refresh the page to see the updated result.
"""

    # Create a new subnote with placeholder content immediately
    subnote_data = NoteCreate(
        title=f"AI Analysis: {tool.name}",
        content=placeholder_content,
        parent_id=apply_data.note_id,
        position=next_position,
    )
    subnote = await note_service.create_note(subnote_data, current_user.id)

    # Prepare the prompt by replacing placeholder
    note_content = f"Title: {note.title}\n\nContent: {note.content or ''}"
    prompt = tool.prompt.replace("[PLACEHOLDER]", note_content)

    # Schedule background task to process AI tool
    background_tasks.add_task(
        process_ai_tool_async,
        subnote.id,
        prompt,
        tool.api_key,
        tool.name,
        current_user.id,
        tool.model,
    )

    logger.info(
        f"User {current_user.id} initiated AI tool {tool.id} on note {note.id}, created subnote {subnote.id}"
    )

    return {
        "message": "AI processing started",
        "subnote_id": subnote.id,
        "tool_name": tool.name,
    }
