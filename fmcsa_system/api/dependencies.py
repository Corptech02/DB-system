"""
FastAPI dependency injection components.
Provides reusable dependencies for database connections, pagination, and authentication.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, Query, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv

from ..database import db_pool
from .models import SearchFilters

# Load environment variables
load_dotenv()

# Optional API key authentication
security = HTTPBearer(auto_error=False)


async def get_db_connection():
    """
    Dependency to get database connection from pool.
    
    Yields:
        Database connection from pool
    """
    if not db_pool.pool:
        await db_pool.initialize()
    
    async with db_pool.acquire() as connection:
        yield connection


async def get_db_pool():
    """
    Dependency to get database pool instance.
    
    Returns:
        Database pool instance
    """
    if not db_pool.pool:
        await db_pool.initialize()
    return db_pool


class PaginationParams:
    """
    Common pagination parameters for list endpoints.
    """
    
    def __init__(
        self,
        limit: Annotated[int, Query(ge=1, le=1000, description="Maximum items to return")] = 100,
        offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
        sort_by: Annotated[str, Query(description="Field to sort by")] = "legal_name",
        sort_order: Annotated[str, Query(regex="^(asc|desc)$", description="Sort order")] = "asc"
    ):
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.sort_order = sort_order
    
    @property
    def has_more(self) -> bool:
        """Check if there might be more results."""
        return self.limit == 1000  # If max limit requested, likely more results


async def get_search_filters(
    # Direct search
    usdot_number: Annotated[Optional[int], Query(description="USDOT number")] = None,
    legal_name: Annotated[Optional[str], Query(description="Legal company name")] = None,
    state: Annotated[Optional[str], Query(max_length=2, description="State code (2 letters)")] = None,
    city: Annotated[Optional[str], Query(description="City name")] = None,
    
    # Filter fields
    entity_type: Annotated[Optional[str], Query(description="Entity type")] = None,
    operating_status: Annotated[Optional[str], Query(description="Operating status")] = None,
    safety_rating: Annotated[Optional[str], Query(description="Safety rating")] = None,
    
    # Insurance filters
    insurance_status: Annotated[Optional[str], Query(description="Insurance status")] = None,
    insurance_expiring_days: Annotated[Optional[int], Query(ge=0, le=365, description="Days until insurance expires")] = None,
    
    # Hazmat filter
    hazmat_only: Annotated[bool, Query(description="Only show hazmat carriers")] = False,
    
    # Range filters
    min_power_units: Annotated[Optional[int], Query(ge=0, description="Minimum power units")] = None,
    max_power_units: Annotated[Optional[int], Query(ge=0, description="Maximum power units")] = None,
    min_drivers: Annotated[Optional[int], Query(ge=0, description="Minimum drivers")] = None,
    max_drivers: Annotated[Optional[int], Query(ge=0, description="Maximum drivers")] = None,
    
    # Pagination
    pagination: PaginationParams = Depends()
) -> SearchFilters:
    """
    Parse and validate search filters from query parameters.
    
    Returns:
        Validated SearchFilters object
    """
    return SearchFilters(
        usdot_number=usdot_number,
        legal_name=legal_name,
        state=state,
        city=city,
        entity_type=entity_type,
        operating_status=operating_status,
        safety_rating=safety_rating,
        insurance_status=insurance_status,
        insurance_expiring_days=insurance_expiring_days,
        hazmat_only=hazmat_only,
        min_power_units=min_power_units,
        max_power_units=max_power_units,
        min_drivers=min_drivers,
        max_drivers=max_drivers,
        limit=pagination.limit,
        offset=pagination.offset,
        sort_by=pagination.sort_by,
        sort_order=pagination.sort_order
    )


async def verify_api_key(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    x_api_key: Annotated[Optional[str], Header()] = None
) -> Optional[str]:
    """
    Optional API key verification.
    
    Args:
        request: FastAPI request object
        credentials: Bearer token from Authorization header
        x_api_key: API key from X-API-Key header
    
    Returns:
        API key if valid or authentication disabled
    
    Raises:
        HTTPException: If authentication required but invalid
    """
    # Check if API key authentication is enabled
    if not os.getenv("ENABLE_API_KEY", "false").lower() == "true":
        return None  # Authentication disabled
    
    # Get expected API key
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        return None  # No key configured
    
    # Check Bearer token
    if credentials and credentials.credentials == expected_key:
        return credentials.credentials
    
    # Check X-API-Key header
    if x_api_key == expected_key:
        return x_api_key
    
    # Check query parameter (for export downloads)
    api_key_param = request.query_params.get("api_key")
    if api_key_param == expected_key:
        return api_key_param
    
    # Authentication required but not provided or invalid
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "Bearer"}
    )


class RateLimiter:
    """
    Simple in-memory rate limiter for API endpoints.
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}
    
    async def check_rate_limit(
        self,
        request: Request,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Check if request exceeds rate limit.
        
        Args:
            request: FastAPI request
            api_key: Optional API key for higher limits
        
        Returns:
            True if within limits
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Use IP address or API key as identifier
        identifier = api_key or request.client.host
        
        # Simplified rate limiting (for production use Redis)
        # This is just a placeholder implementation
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    api_key: Annotated[Optional[str], Depends(verify_api_key)] = None
):
    """
    Dependency to check rate limits.
    
    Args:
        request: FastAPI request
        api_key: Verified API key
    
    Raises:
        HTTPException: If rate limit exceeded
    """
    await rate_limiter.check_rate_limit(request, api_key)


class DatabaseSession:
    """
    Context manager for database operations in requests.
    Ensures proper connection handling and cleanup.
    """
    
    def __init__(self, request: Request):
        self.request = request
    
    async def __aenter__(self):
        """Acquire database connection."""
        if not hasattr(self.request.app.state, "db_pool"):
            self.request.app.state.db_pool = db_pool
            await db_pool.initialize()
        
        self.connection = await db_pool.pool.acquire()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release database connection."""
        if hasattr(self, "connection"):
            await db_pool.pool.release(self.connection)


async def get_db_session(request: Request) -> DatabaseSession:
    """
    Get database session for request.
    
    Args:
        request: FastAPI request
    
    Returns:
        Database session context manager
    """
    return DatabaseSession(request)