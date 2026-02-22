"""
Session Service
Handles session creation, updates, and country code detection
"""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, cast, String as SQLString
from datetime import datetime
import random
import string

from app.models.session import Session
from app.models.user import User
from app.core.centralized_logger import get_logger
from app.core.config import settings
from app.services.geolocation import extract_client_ip, detect_country_from_ip

logger = get_logger(__name__)


async def get_or_create_session(
    db: AsyncSession,
    request,
    session_id: str,
    user_id: Optional[int] = None,
    current_user: Optional[dict] = None
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Get existing session or create new one with country detection

    Args:
        db: Database session
        request: FastAPI Request object (for IP extraction)
        session_id: Client-provided session UUID string
        user_id: Optional user ID from frontend (for anonymous users)
        current_user: Authenticated user dict (if logged in)

    Returns:
        Tuple of (database session ID, user ID, country_code), or (None, None, None) on error
    """
    try:
        # Check if session exists
        stmt = select(Session).where(
            cast(Session.meta['client_session_id'], SQLString) == session_id
        )
        result = await db.execute(stmt)
        existing_session = result.scalar_one_or_none()

        if existing_session:
            # Update last_seen_at
            existing_session.last_seen_at = datetime.utcnow()

            # Detect and update country_code if not set
            if not existing_session.country_code:
                client_ip = extract_client_ip(request)
                country_code = await detect_country_from_ip(client_ip)
                existing_session.country_code = country_code
                logger.info(f"[GeoLocation] IP: {client_ip} → Country: {country_code} (Updated existing session {session_id})")

            await db.commit()
            logger.debug(f"Session {session_id} exists (DB ID: {existing_session.id})")
            return existing_session.id, existing_session.user_id, existing_session.country_code

        # Session doesn't exist - detect country and create session
        client_ip = extract_client_ip(request)
        country_code = await detect_country_from_ip(client_ip)
        logger.info(f"[GeoLocation] IP: {client_ip} → Country: {country_code} (New session)")

        # Determine user based on authentication status or provided user_id
        user = await _get_or_create_user(db, user_id, current_user)

        # Create session with country code
        new_session = Session(
            user_id=user.id,
            started_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            country_code=country_code,
            meta={
                "source": "chat_api",
                "auto_created": True,
                "authenticated": current_user is not None,
                "client_session_id": session_id
            }
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)

        logger.info(f"Created session: client_id={session_id}, db_id={new_session.id}, country={country_code} for user {user.email}")
        return new_session.id, user.id, country_code

    except Exception as e:
        logger.error(f"Failed to get/create session: {e}", exc_info=True)
        await db.rollback()
        return None, None, None


async def _get_or_create_user(
    db: AsyncSession,
    user_id: Optional[int],
    current_user: Optional[dict]
) -> User:
    """
    Get existing user or create new anonymous user

    Args:
        db: Database session
        user_id: Optional user ID from frontend
        current_user: Authenticated user dict

    Returns:
        User object
    """
    if current_user:
        # Authenticated user - find or create
        user_email = f"{current_user['username']}@reviewguide.ai"
        stmt = select(User).where(User.email == user_email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=user_email,
                locale="en",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            await db.flush()
            logger.info(f"Created authenticated user: {user_email} ({user.id})")
        return user

    elif user_id:
        # Anonymous user with existing user_id - try to reuse
        # SECURITY: Only honor client-supplied user_id if it maps to an anonymous account.
        # Authenticated accounts must not be claimable by anonymous clients.
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Only allow reuse if this is an anonymous account (email matches anonymous prefix)
            if user.email and user.email.startswith(settings.ANONYMOUS_EMAIL_PREFIX):
                logger.info(f"Reusing existing anonymous user: {user.email} ({user.id})")
                return user
            else:
                # Client is trying to claim an authenticated user's ID — deny and create new
                logger.warning(
                    f"[security] Anonymous request attempted to claim authenticated user_id={user_id} "
                    f"(email={user.email}). Creating new anonymous user instead."
                )
        else:
            logger.warning(f"user_id {user_id} not found, creating new user")

    # Create new anonymous user
    random_suffix = ''.join(
        random.choices(
            string.ascii_lowercase + string.digits,
            k=settings.ANONYMOUS_EMAIL_RANDOM_LENGTH
        )
    )
    user_email = f"{settings.ANONYMOUS_EMAIL_PREFIX}{random_suffix}{settings.ANONYMOUS_EMAIL_DOMAIN}"
    user = User(
        email=user_email,
        locale="en",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(user)
    await db.flush()
    logger.info(f"Created new anonymous user: {user_email} ({user.id})")
    return user
