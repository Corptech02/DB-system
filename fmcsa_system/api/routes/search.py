"""
Search endpoints for FMCSA carriers.
Provides search, filtering, and detail retrieval capabilities.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from uuid import UUID

from ...database import db_pool, get_carrier_by_usdot, get_insurance_expiring_soon
from ..models import (
    CarrierResponse,
    CarrierSummary,
    SearchFilters,
    PaginatedResponse,
    InsuranceStatus
)
from ..dependencies import get_db_pool, get_search_filters, check_rate_limit

router = APIRouter()


@router.get("/carriers", response_model=PaginatedResponse)
async def search_carriers(
    filters: SearchFilters = Depends(get_search_filters),
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> PaginatedResponse:
    """
    Search carriers with filters and pagination.
    
    Supports filtering by:
    - USDOT number
    - State
    - Entity type
    - Operating status
    - Insurance expiration
    - Power units and drivers ranges
    
    Returns paginated results with metadata.
    """
    try:
        # Build query
        where_clauses = []
        params = []
        param_count = 0
        
        # Direct filters
        if filters.usdot_number:
            param_count += 1
            where_clauses.append(f"usdot_number = ${param_count}")
            params.append(filters.usdot_number)
        
        if filters.legal_name:
            param_count += 1
            where_clauses.append(f"legal_name ILIKE ${param_count}")
            params.append(f"%{filters.legal_name}%")
        
        if filters.state:
            param_count += 1
            where_clauses.append(f"physical_state = ${param_count}")
            params.append(filters.state.upper())
        
        if filters.city:
            param_count += 1
            where_clauses.append(f"physical_city ILIKE ${param_count}")
            params.append(f"%{filters.city}%")
        
        if filters.entity_type:
            param_count += 1
            where_clauses.append(f"entity_type = ${param_count}")
            params.append(filters.entity_type)
        
        if filters.operating_status:
            param_count += 1
            where_clauses.append(f"operating_status = ${param_count}")
            params.append(filters.operating_status)
        
        if filters.safety_rating:
            param_count += 1
            where_clauses.append(f"safety_rating = ${param_count}")
            params.append(filters.safety_rating)
        
        # Insurance filters
        if filters.insurance_expiring_days:
            param_count += 1
            where_clauses.append(
                f"liability_insurance_date BETWEEN CURRENT_DATE "
                f"AND CURRENT_DATE + INTERVAL '1 day' * ${param_count}"
            )
            params.append(filters.insurance_expiring_days)
        
        elif filters.insurance_status:
            if filters.insurance_status == InsuranceStatus.EXPIRED:
                where_clauses.append("liability_insurance_date < CURRENT_DATE")
            elif filters.insurance_status == InsuranceStatus.EXPIRING_SOON:
                where_clauses.append(
                    "liability_insurance_date BETWEEN CURRENT_DATE "
                    "AND CURRENT_DATE + INTERVAL '30 days'"
                )
            elif filters.insurance_status == InsuranceStatus.VALID:
                where_clauses.append("liability_insurance_date > CURRENT_DATE + INTERVAL '90 days'")
        
        # Hazmat filter
        if filters.hazmat_only:
            where_clauses.append("hazmat_flag = TRUE")
        
        # Range filters
        if filters.min_power_units:
            param_count += 1
            where_clauses.append(f"power_units >= ${param_count}")
            params.append(filters.min_power_units)
        
        if filters.max_power_units:
            param_count += 1
            where_clauses.append(f"power_units <= ${param_count}")
            params.append(filters.max_power_units)
        
        if filters.min_drivers:
            param_count += 1
            where_clauses.append(f"drivers >= ${param_count}")
            params.append(filters.min_drivers)
        
        if filters.max_drivers:
            param_count += 1
            where_clauses.append(f"drivers <= ${param_count}")
            params.append(filters.max_drivers)
        
        # Build WHERE clause
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM carriers WHERE {where_sql}"
        total_count = await db.fetchval(count_query, *params)
        
        # Build main query with sorting and pagination
        order_column = filters.sort_by
        if order_column not in ["legal_name", "usdot_number", "physical_state", "created_at"]:
            order_column = "legal_name"
        
        order_direction = "DESC" if filters.sort_order == "desc" else "ASC"
        
        param_count += 1
        limit_param = param_count
        params.append(filters.limit)
        
        param_count += 1
        offset_param = param_count
        params.append(filters.offset)
        
        query = f"""
            SELECT 
                id,
                usdot_number,
                legal_name,
                dba_name,
                physical_address,
                physical_city,
                physical_state,
                physical_zip,
                telephone,
                email,
                entity_type,
                operating_status,
                power_units,
                drivers,
                liability_insurance_date,
                liability_insurance_amount,
                safety_rating,
                hazmat_flag,
                created_at,
                updated_at,
                CASE 
                    WHEN liability_insurance_date IS NULL THEN NULL
                    ELSE (liability_insurance_date - CURRENT_DATE)::INTEGER
                END as days_until_insurance_expiration
            FROM carriers
            WHERE {where_sql}
            ORDER BY {order_column} {order_direction}
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        
        # Execute query
        rows = await db.fetch(query, *params)
        
        # Convert to response models
        carriers = []
        for row in rows:
            carrier_dict = dict(row)
            carrier = CarrierSummary(**carrier_dict)
            
            # Calculate insurance status
            if carrier_dict.get("days_until_insurance_expiration") is not None:
                days = carrier_dict["days_until_insurance_expiration"]
                if days < 0:
                    carrier.insurance_status = InsuranceStatus.EXPIRED
                elif days <= 30:
                    carrier.insurance_status = InsuranceStatus.EXPIRING_SOON
                elif days <= 60:
                    carrier.insurance_status = InsuranceStatus.EXPIRING_60_DAYS
                elif days <= 90:
                    carrier.insurance_status = InsuranceStatus.EXPIRING_90_DAYS
                else:
                    carrier.insurance_status = InsuranceStatus.VALID
            
            carriers.append(carrier)
        
        return PaginatedResponse(
            data=carriers,
            total=total_count,
            limit=filters.limit,
            offset=filters.offset,
            has_more=(filters.offset + filters.limit) < total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/carriers/{usdot_number}", response_model=CarrierResponse)
async def get_carrier(
    usdot_number: int = Path(..., description="USDOT number"),
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> CarrierResponse:
    """
    Get detailed carrier information by USDOT number.
    
    Args:
        usdot_number: USDOT number of the carrier
    
    Returns:
        Complete carrier information
    
    Raises:
        404: Carrier not found
    """
    try:
        # Query for carrier
        query = """
            SELECT 
                *,
                CASE 
                    WHEN liability_insurance_date IS NOT NULL 
                    THEN (liability_insurance_date - CURRENT_DATE)::INTEGER
                    ELSE NULL
                END as days_until_insurance_expiration
            FROM carriers
            WHERE usdot_number = $1
        """
        
        result = await db.fetchrow(query, usdot_number)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Carrier with USDOT number {usdot_number} not found"
            )
        
        # Convert to response model
        carrier_dict = dict(result)
        carrier = CarrierResponse(**carrier_dict)
        
        return carrier
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get carrier: {str(e)}")


@router.get("/carriers/expiring", response_model=List[CarrierSummary])
async def get_expiring_insurance(
    days: int = Query(30, ge=1, le=365, description="Days ahead to check"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> List[CarrierSummary]:
    """
    Get carriers with insurance expiring soon.
    
    Args:
        days: Number of days ahead to check (default 30)
        limit: Maximum number of results
    
    Returns:
        List of carriers with expiring insurance
    """
    try:
        # Use the database function
        query = """
            SELECT * FROM get_insurance_expiring($1)
            LIMIT $2
        """
        
        rows = await db.fetch(query, days, limit)
        
        carriers = []
        for row in rows:
            carrier_dict = dict(row)
            
            # Map fields for CarrierSummary
            summary = CarrierSummary(
                id=carrier_dict.get("id"),
                usdot_number=carrier_dict["usdot_number"],
                legal_name=carrier_dict["legal_name"],
                dba_name=carrier_dict.get("dba_name"),
                physical_state=carrier_dict.get("physical_state"),
                physical_city=None,  # Not in function result
                operating_status="ACTIVE",  # Function only returns active
                entity_type=None,
                insurance_status=InsuranceStatus.EXPIRING_SOON,
                days_until_insurance_expiration=carrier_dict.get("days_until_expiration")
            )
            carriers.append(summary)
        
        return carriers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get expiring insurance: {str(e)}")


@router.get("/carriers/search/name", response_model=List[CarrierSummary])
async def search_by_name(
    q: str = Query(..., min_length=3, description="Search term"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> List[CarrierSummary]:
    """
    Search carriers by name using fuzzy matching.
    
    Uses PostgreSQL trigram similarity for fuzzy search.
    
    Args:
        q: Search query (minimum 3 characters)
        limit: Maximum results
    
    Returns:
        List of matching carriers sorted by similarity
    """
    try:
        # Use the trigram search function
        query = """
            SELECT * FROM search_carriers_by_name($1, $2)
        """
        
        rows = await db.fetch(query, q, 0.3)  # 0.3 similarity threshold
        
        # Limit results
        rows = rows[:limit]
        
        carriers = []
        for row in rows:
            carrier_dict = dict(row)
            summary = CarrierSummary(
                id=carrier_dict["id"],
                usdot_number=carrier_dict["usdot_number"],
                legal_name=carrier_dict["legal_name"],
                dba_name=carrier_dict.get("dba_name"),
                physical_state=carrier_dict.get("physical_state"),
                physical_city=None,
                operating_status=carrier_dict.get("operating_status"),
                entity_type=None
            )
            carriers.append(summary)
        
        return carriers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Name search failed: {str(e)}")