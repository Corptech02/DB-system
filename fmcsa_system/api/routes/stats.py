"""
Statistics endpoints for FMCSA carrier data.
Provides aggregated statistics and analytics.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
import logging

from ...database import db_pool, refresh_statistics
from ..models import StatisticsResponse
from ..dependencies import check_rate_limit, get_db_pool

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics(
    state: Optional[str] = None,
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> StatisticsResponse:
    """
    Get carrier statistics.
    
    Returns aggregated statistics including:
    - Total and active carrier counts
    - Breakdown by state, entity type, and operating status
    - Insurance expiration statistics
    - Average fleet sizes
    
    Args:
        state: Optional state filter
    
    Returns:
        Comprehensive statistics
    """
    try:
        # Get basic counts
        total_query = "SELECT COUNT(*) FROM carriers"
        active_query = "SELECT COUNT(*) FROM carriers WHERE operating_status = 'ACTIVE'"
        
        if state:
            total_query += f" WHERE physical_state = '{state}'"
            active_query += f" AND physical_state = '{state}'"
        
        total_carriers = await db.fetchval(total_query)
        active_carriers = await db.fetchval(active_query)
        inactive_carriers = total_carriers - active_carriers
        
        # Get breakdown by state
        state_query = """
            SELECT physical_state, COUNT(*) as count
            FROM carriers
            WHERE physical_state IS NOT NULL
            GROUP BY physical_state
            ORDER BY count DESC
            LIMIT 50
        """
        state_rows = await db.fetch(state_query)
        by_state = {row['physical_state']: row['count'] for row in state_rows}
        
        # Get breakdown by entity type
        entity_query = """
            SELECT entity_type, COUNT(*) as count
            FROM carriers
            WHERE entity_type IS NOT NULL
            GROUP BY entity_type
            ORDER BY count DESC
        """
        entity_rows = await db.fetch(entity_query)
        by_entity_type = {row['entity_type']: row['count'] for row in entity_rows}
        
        # Get breakdown by operating status
        status_query = """
            SELECT operating_status, COUNT(*) as count
            FROM carriers
            WHERE operating_status IS NOT NULL
            GROUP BY operating_status
            ORDER BY count DESC
        """
        status_rows = await db.fetch(status_query)
        by_operating_status = {row['operating_status']: row['count'] for row in status_rows}
        
        # Get insurance statistics
        insurance_query = """
            SELECT 
                COUNT(CASE WHEN liability_insurance_date < CURRENT_DATE THEN 1 END) as expired,
                COUNT(CASE WHEN liability_insurance_date BETWEEN CURRENT_DATE 
                    AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_30,
                COUNT(CASE WHEN liability_insurance_date BETWEEN CURRENT_DATE + INTERVAL '30 days'
                    AND CURRENT_DATE + INTERVAL '60 days' THEN 1 END) as expiring_60,
                COUNT(CASE WHEN liability_insurance_date BETWEEN CURRENT_DATE + INTERVAL '60 days'
                    AND CURRENT_DATE + INTERVAL '90 days' THEN 1 END) as expiring_90,
                COUNT(CASE WHEN liability_insurance_date > CURRENT_DATE + INTERVAL '90 days' THEN 1 END) as valid,
                COUNT(CASE WHEN liability_insurance_date IS NULL THEN 1 END) as unknown
            FROM carriers
            WHERE operating_status = 'ACTIVE'
        """
        
        if state:
            insurance_query += f" AND physical_state = '{state}'"
        
        insurance_row = await db.fetchrow(insurance_query)
        insurance_stats = {
            "expired": insurance_row['expired'],
            "expiring_30_days": insurance_row['expiring_30'],
            "expiring_60_days": insurance_row['expiring_60'],
            "expiring_90_days": insurance_row['expiring_90'],
            "valid": insurance_row['valid'],
            "unknown": insurance_row['unknown']
        }
        
        # Get hazmat count
        hazmat_query = "SELECT COUNT(*) FROM carriers WHERE hazmat_flag = TRUE"
        if state:
            hazmat_query += f" AND physical_state = '{state}'"
        hazmat_carriers = await db.fetchval(hazmat_query)
        
        # Get averages
        avg_query = """
            SELECT 
                AVG(power_units) as avg_power_units,
                AVG(drivers) as avg_drivers
            FROM carriers
            WHERE operating_status = 'ACTIVE'
                AND power_units IS NOT NULL
                AND drivers IS NOT NULL
        """
        if state:
            avg_query += f" AND physical_state = '{state}'"
        
        avg_row = await db.fetchrow(avg_query)
        avg_power_units = float(avg_row['avg_power_units'] or 0)
        avg_drivers = float(avg_row['avg_drivers'] or 0)
        
        # Get last update time
        last_update_query = "SELECT MAX(updated_at) FROM carriers"
        last_updated = await db.fetchval(last_update_query)
        
        return StatisticsResponse(
            total_carriers=total_carriers,
            active_carriers=active_carriers,
            inactive_carriers=inactive_carriers,
            by_state=by_state,
            by_entity_type=by_entity_type,
            by_operating_status=by_operating_status,
            insurance_stats=insurance_stats,
            hazmat_carriers=hazmat_carriers,
            avg_power_units=avg_power_units,
            avg_drivers=avg_drivers,
            last_updated=last_updated
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/stats/summary")
async def get_summary_stats(
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Get quick summary statistics.
    
    Returns basic counts and key metrics for dashboard display.
    """
    try:
        query = """
            SELECT 
                COUNT(*) as total_carriers,
                COUNT(CASE WHEN operating_status = 'ACTIVE' THEN 1 END) as active_carriers,
                COUNT(CASE WHEN liability_insurance_date < CURRENT_DATE THEN 1 END) as expired_insurance,
                COUNT(CASE WHEN liability_insurance_date BETWEEN CURRENT_DATE 
                    AND CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as expiring_soon,
                COUNT(CASE WHEN hazmat_flag = TRUE THEN 1 END) as hazmat_carriers,
                COUNT(DISTINCT physical_state) as states_covered
            FROM carriers
        """
        
        result = await db.fetchrow(query)
        
        return {
            "total_carriers": result['total_carriers'],
            "active_carriers": result['active_carriers'],
            "expired_insurance": result['expired_insurance'],
            "expiring_soon": result['expiring_soon'],
            "hazmat_carriers": result['hazmat_carriers'],
            "states_covered": result['states_covered']
        }
        
    except Exception as e:
        logger.error(f"Failed to get summary stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary stats: {str(e)}")


@router.get("/stats/top-states")
async def get_top_states(
    limit: int = 10,
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> List[Dict[str, Any]]:
    """
    Get top states by carrier count.
    
    Args:
        limit: Number of states to return
    
    Returns:
        List of states with carrier counts
    """
    try:
        query = """
            SELECT 
                physical_state as state,
                COUNT(*) as total_carriers,
                COUNT(CASE WHEN operating_status = 'ACTIVE' THEN 1 END) as active_carriers,
                AVG(power_units) as avg_fleet_size
            FROM carriers
            WHERE physical_state IS NOT NULL
            GROUP BY physical_state
            ORDER BY total_carriers DESC
            LIMIT $1
        """
        
        rows = await db.fetch(query, limit)
        
        return [
            {
                "state": row['state'],
                "total_carriers": row['total_carriers'],
                "active_carriers": row['active_carriers'],
                "avg_fleet_size": float(row['avg_fleet_size']) if row['avg_fleet_size'] else 0
            }
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Failed to get top states: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get top states: {str(e)}")


@router.get("/stats/insurance-expiration-forecast")
async def get_insurance_forecast(
    days: int = 90,
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> Dict[str, Any]:
    """
    Get insurance expiration forecast.
    
    Shows how many carriers have insurance expiring in different time windows.
    
    Args:
        days: Maximum days to forecast
    
    Returns:
        Insurance expiration forecast by time window
    """
    try:
        query = """
            SELECT 
                COUNT(CASE WHEN days_until <= 7 THEN 1 END) as week_1,
                COUNT(CASE WHEN days_until > 7 AND days_until <= 14 THEN 1 END) as week_2,
                COUNT(CASE WHEN days_until > 14 AND days_until <= 30 THEN 1 END) as month_1,
                COUNT(CASE WHEN days_until > 30 AND days_until <= 60 THEN 1 END) as month_2,
                COUNT(CASE WHEN days_until > 60 AND days_until <= 90 THEN 1 END) as month_3,
                COUNT(CASE WHEN days_until > 90 THEN 1 END) as beyond_90
            FROM (
                SELECT (liability_insurance_date - CURRENT_DATE)::INTEGER as days_until
                FROM carriers
                WHERE operating_status = 'ACTIVE'
                    AND liability_insurance_date >= CURRENT_DATE
                    AND liability_insurance_date <= CURRENT_DATE + INTERVAL '1 day' * $1
            ) t
        """
        
        result = await db.fetchrow(query, days)
        
        return {
            "forecast_days": days,
            "expiring_week_1": result['week_1'],
            "expiring_week_2": result['week_2'],
            "expiring_month_1": result['month_1'],
            "expiring_month_2": result['month_2'],
            "expiring_month_3": result['month_3'],
            "expiring_beyond_90": result['beyond_90']
        }
        
    except Exception as e:
        logger.error(f"Failed to get insurance forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insurance forecast: {str(e)}")


@router.post("/stats/refresh")
async def refresh_stats(
    _: None = Depends(check_rate_limit),
    db: Any = Depends(get_db_pool)
) -> Dict[str, str]:
    """
    Refresh materialized view for carrier statistics.
    
    This should be called periodically (e.g., daily) to update cached statistics.
    
    Returns:
        Confirmation message
    """
    try:
        await refresh_statistics()
        return {"status": "success", "message": "Statistics refreshed successfully"}
        
    except Exception as e:
        logger.error(f"Failed to refresh statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh statistics: {str(e)}")