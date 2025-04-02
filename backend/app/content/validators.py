"""
Input validators for content analysis requests.
Enforces text length limits and image format/size constraints.
"""

import hashlib
from fastapi import HTTPException, UploadFile, status
from app.config import settings


def validate_text_input(text: str) -> str:
    """
    Validate text input against configured limits.

    Rules:
    - Max 5,000 words or 30,000 characters
    - Must not be empty or whitespace-only

    Returns sanitized text (stripped whitespace).
    Raises HTTPException on violation.
    """
    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text input cannot be empty",
        )

    word_count = len(text.split())
    if word_count > settings.MAX_TEXT_WORDS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Text exceeds maximum of {settings.MAX_TEXT_WORDS} words (got {word_count})",
        )

    if len(text) > settings.MAX_TEXT_CHARS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Text exceeds maximum of {settings.MAX_TEXT_CHARS} characters (got {len(text)})",
        )

    return text


async def validate_image_upload(file: UploadFile) -> bytes:
    """
    Validate image upload against configured limits.

    Rules:
    - Max 10MB
    - Only JPEG, PNG, WebP allowed
    - Must be a valid image file

    Returns raw image bytes.
    Raises HTTPException on violation.
    """
    if file.content_type not in settings.ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Image format '{file.content_type}' not supported. Allowed: {settings.ALLOWED_IMAGE_FORMATS}",
        )

    content = await file.read()
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds {settings.MAX_IMAGE_SIZE_MB}MB limit",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    return content


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
