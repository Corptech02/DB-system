"""
Lead generation service for identifying insurance expiration opportunities.
Scores and prioritizes carriers based on various criteria.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from ..database import db_pool
from ..api.models import InsuranceStatus

logger = logging.getLogger(__name__)


class LeadScore(Enum):
    """Lead quality scores."""
    HOT = "hot"  # Expiring within 30 days
    WARM = "warm"  # Expiring within 60 days
    COOL = "cool"  # Expiring within 90 days
    COLD = "cold"  # Expired or far future


@dataclass
class Lead:
    """Lead information for a carrier."""
    usdot_number: int
    legal_name: str
    dba_name: Optional[str]
    state: str
    city: Optional[str]
    telephone: Optional[str]
    email: Optional[str]
    
    # Insurance information
    liability_insurance_date: Optional[date]
    liability_insurance_amount: Optional[float]
    days_until_expiration: Optional[int]
    insurance_status: InsuranceStatus
    
    # Business information
    entity_type: Optional[str]
    operating_status: str
    power_units: Optional[int]
    drivers: Optional[int]
    safety_rating: Optional[str]
    
    # Lead scoring
    lead_score: LeadScore
    score_value: int  # 0-100
    score_reasons: List[str]
    
    # Contact priority
    priority: int  # 1-5, where 1 is highest
    best_contact_method: str  # "phone", "email", "mail"


class LeadGenerator:
    """
    Service for generating and scoring insurance leads.
    """
    
    def __init__(self):
        """Initialize lead generator."""
        pass
    
    async def get_expiring_insurance_leads(
        self,
        days_ahead: int = 90,
        state: Optional[str] = None,
        min_power_units: Optional[int] = None,
        min_insurance_amount: Optional[float] = None,
        limit: int = 100
    ) -> List[Lead]:
        """
        Get leads for carriers with expiring insurance.
        
        Args:
            days_ahead: Look ahead period in days
            state: Filter by state
            min_power_units: Minimum fleet size
            min_insurance_amount: Minimum current insurance
            limit: Maximum results
        
        Returns:
            List of scored and prioritized leads
        """
        # Build query
        where_clauses = [
            "liability_insurance_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 day' * $1",
            "operating_status = 'ACTIVE'"
        ]
        params = [days_ahead]
        param_count = 1
        
        if state:
            param_count += 1
            where_clauses.append(f"physical_state = ${param_count}")
            params.append(state)
        
        if min_power_units:
            param_count += 1
            where_clauses.append(f"power_units >= ${param_count}")
            params.append(min_power_units)
        
        if min_insurance_amount:
            param_count += 1
            where_clauses.append(f"liability_insurance_amount >= ${param_count}")
            params.append(min_insurance_amount)
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                usdot_number,
                legal_name,
                dba_name,
                physical_state,
                physical_city,
                telephone,
                email,
                liability_insurance_date,
                liability_insurance_amount,
                (liability_insurance_date - CURRENT_DATE)::INTEGER as days_until_expiration,
                entity_type,
                operating_status,
                power_units,
                drivers,
                safety_rating,
                hazmat_flag,
                mcs_150_date,
                cargo_carried
            FROM carriers
            WHERE {where_sql}
            ORDER BY liability_insurance_date, power_units DESC NULLS LAST
            LIMIT {limit}
        """
        
        rows = await db_pool.fetch(query, *params)
        
        # Convert to Lead objects with scoring
        leads = []
        for row in rows:
            lead = self._create_lead_from_row(dict(row))
            leads.append(lead)
        
        # Sort by priority
        leads.sort(key=lambda x: (x.priority, -x.score_value))
        
        return leads
    
    async def get_expired_insurance_leads(
        self,
        max_days_expired: int = 30,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Lead]:
        """
        Get leads for carriers with recently expired insurance.
        
        Args:
            max_days_expired: Maximum days since expiration
            state: Filter by state
            limit: Maximum results
        
        Returns:
            List of carriers with expired insurance
        """
        where_clauses = [
            "liability_insurance_date < CURRENT_DATE",
            "liability_insurance_date >= CURRENT_DATE - INTERVAL '1 day' * $1",
            "operating_status = 'ACTIVE'"
        ]
        params = [max_days_expired]
        param_count = 1
        
        if state:
            param_count += 1
            where_clauses.append(f"physical_state = ${param_count}")
            params.append(state)
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                usdot_number,
                legal_name,
                dba_name,
                physical_state,
                physical_city,
                telephone,
                email,
                liability_insurance_date,
                liability_insurance_amount,
                (CURRENT_DATE - liability_insurance_date)::INTEGER as days_expired,
                entity_type,
                operating_status,
                power_units,
                drivers,
                safety_rating
            FROM carriers
            WHERE {where_sql}
            ORDER BY liability_insurance_date DESC, power_units DESC NULLS LAST
            LIMIT {limit}
        """
        
        rows = await db_pool.fetch(query, *params)
        
        leads = []
        for row in rows:
            data = dict(row)
            # Convert days_expired to negative days_until_expiration
            data['days_until_expiration'] = -data.pop('days_expired', 0)
            lead = self._create_lead_from_row(data)
            leads.append(lead)
        
        return leads
    
    async def get_high_value_leads(
        self,
        min_power_units: int = 10,
        min_drivers: int = 10,
        days_ahead: int = 90,
        limit: int = 100
    ) -> List[Lead]:
        """
        Get high-value leads based on fleet size.
        
        Args:
            min_power_units: Minimum power units
            min_drivers: Minimum drivers
            days_ahead: Insurance expiration window
            limit: Maximum results
        
        Returns:
            List of high-value leads
        """
        query = """
            SELECT 
                usdot_number,
                legal_name,
                dba_name,
                physical_state,
                physical_city,
                telephone,
                email,
                liability_insurance_date,
                liability_insurance_amount,
                CASE 
                    WHEN liability_insurance_date IS NOT NULL 
                    THEN (liability_insurance_date - CURRENT_DATE)::INTEGER
                    ELSE NULL
                END as days_until_expiration,
                entity_type,
                operating_status,
                power_units,
                drivers,
                safety_rating,
                hazmat_flag
            FROM carriers
            WHERE 
                operating_status = 'ACTIVE'
                AND power_units >= $1
                AND drivers >= $2
                AND (
                    liability_insurance_date IS NULL
                    OR liability_insurance_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 day' * $3
                )
            ORDER BY 
                CASE 
                    WHEN liability_insurance_date IS NULL THEN 0
                    ELSE (liability_insurance_date - CURRENT_DATE)::INTEGER
                END,
                power_units DESC
            LIMIT $4
        """
        
        rows = await db_pool.fetch(query, min_power_units, min_drivers, days_ahead, limit)
        
        leads = []
        for row in rows:
            lead = self._create_lead_from_row(dict(row))
            # Boost score for high-value leads
            lead.score_value = min(100, lead.score_value + 20)
            lead.score_reasons.append("High-value fleet")
            leads.append(lead)
        
        return leads
    
    def _create_lead_from_row(self, data: Dict[str, Any]) -> Lead:
        """
        Create a Lead object from database row.
        
        Args:
            data: Row data dictionary
        
        Returns:
            Scored Lead object
        """
        # Determine insurance status
        days_until = data.get('days_until_expiration')
        if days_until is None:
            insurance_status = InsuranceStatus.UNKNOWN
        elif days_until < 0:
            insurance_status = InsuranceStatus.EXPIRED
        elif days_until <= 30:
            insurance_status = InsuranceStatus.EXPIRING_SOON
        elif days_until <= 60:
            insurance_status = InsuranceStatus.EXPIRING_60_DAYS
        elif days_until <= 90:
            insurance_status = InsuranceStatus.EXPIRING_90_DAYS
        else:
            insurance_status = InsuranceStatus.VALID
        
        # Calculate lead score
        lead_score, score_value, score_reasons = self._calculate_lead_score(
            days_until,
            insurance_status,
            data.get('power_units'),
            data.get('drivers'),
            data.get('safety_rating'),
            data.get('hazmat_flag', False)
        )
        
        # Determine priority
        priority = self._calculate_priority(lead_score, score_value)
        
        # Determine best contact method
        best_contact = self._determine_contact_method(
            data.get('telephone'),
            data.get('email')
        )
        
        return Lead(
            usdot_number=data['usdot_number'],
            legal_name=data['legal_name'],
            dba_name=data.get('dba_name'),
            state=data.get('physical_state', ''),
            city=data.get('physical_city'),
            telephone=data.get('telephone'),
            email=data.get('email'),
            liability_insurance_date=data.get('liability_insurance_date'),
            liability_insurance_amount=data.get('liability_insurance_amount'),
            days_until_expiration=days_until,
            insurance_status=insurance_status,
            entity_type=data.get('entity_type'),
            operating_status=data.get('operating_status', 'ACTIVE'),
            power_units=data.get('power_units'),
            drivers=data.get('drivers'),
            safety_rating=data.get('safety_rating'),
            lead_score=lead_score,
            score_value=score_value,
            score_reasons=score_reasons,
            priority=priority,
            best_contact_method=best_contact
        )
    
    def _calculate_lead_score(
        self,
        days_until_expiration: Optional[int],
        insurance_status: InsuranceStatus,
        power_units: Optional[int],
        drivers: Optional[int],
        safety_rating: Optional[str],
        hazmat: bool
    ) -> Tuple[LeadScore, int, List[str]]:
        """
        Calculate lead score based on various factors.
        
        Returns:
            Tuple of (lead_score, numeric_score, reasons)
        """
        score = 50  # Base score
        reasons = []
        
        # Insurance timing (most important factor)
        if insurance_status == InsuranceStatus.EXPIRED:
            score += 30
            reasons.append("Insurance recently expired")
            lead_score = LeadScore.HOT
        elif insurance_status == InsuranceStatus.EXPIRING_SOON:
            score += 40
            reasons.append("Insurance expiring within 30 days")
            lead_score = LeadScore.HOT
        elif insurance_status == InsuranceStatus.EXPIRING_60_DAYS:
            score += 25
            reasons.append("Insurance expiring within 60 days")
            lead_score = LeadScore.WARM
        elif insurance_status == InsuranceStatus.EXPIRING_90_DAYS:
            score += 15
            reasons.append("Insurance expiring within 90 days")
            lead_score = LeadScore.COOL
        else:
            lead_score = LeadScore.COLD
        
        # Fleet size
        if power_units:
            if power_units >= 50:
                score += 15
                reasons.append("Large fleet (50+ units)")
            elif power_units >= 20:
                score += 10
                reasons.append("Medium fleet (20-49 units)")
            elif power_units >= 5:
                score += 5
                reasons.append("Small fleet (5-19 units)")
        
        # Driver count
        if drivers and drivers >= 50:
            score += 5
            reasons.append("Large driver pool")
        
        # Safety rating
        if safety_rating == "SATISFACTORY":
            score += 5
            reasons.append("Good safety rating")
        elif safety_rating in ["CONDITIONAL", "UNSATISFACTORY"]:
            score -= 10
            reasons.append("Poor safety rating")
        
        # Hazmat
        if hazmat:
            score += 5
            reasons.append("Hazmat carrier")
        
        # Cap score at 100
        score = min(100, max(0, score))
        
        return lead_score, score, reasons
    
    def _calculate_priority(self, lead_score: LeadScore, score_value: int) -> int:
        """
        Calculate contact priority (1-5, where 1 is highest).
        
        Args:
            lead_score: Lead temperature
            score_value: Numeric score
        
        Returns:
            Priority level
        """
        if lead_score == LeadScore.HOT and score_value >= 80:
            return 1
        elif lead_score == LeadScore.HOT:
            return 2
        elif lead_score == LeadScore.WARM and score_value >= 70:
            return 2
        elif lead_score == LeadScore.WARM:
            return 3
        elif lead_score == LeadScore.COOL:
            return 4
        else:
            return 5
    
    def _determine_contact_method(
        self,
        telephone: Optional[str],
        email: Optional[str]
    ) -> str:
        """
        Determine best contact method.
        
        Args:
            telephone: Phone number
            email: Email address
        
        Returns:
            Recommended contact method
        """
        if telephone and email:
            return "phone"  # Phone typically more effective
        elif telephone:
            return "phone"
        elif email:
            return "email"
        else:
            return "mail"  # Fallback to physical mail
    
    def calculate_expiration_status(
        self,
        insurance_date: Optional[date]
    ) -> str:
        """
        Calculate insurance expiration status.
        
        Args:
            insurance_date: Insurance expiration date
        
        Returns:
            Status string
        """
        if not insurance_date:
            return "unknown"
        
        days = (insurance_date - date.today()).days
        
        if days < 0:
            return "expired"
        elif days <= 30:
            return "expiring_soon"
        elif days <= 60:
            return "expiring_60_days"
        elif days <= 90:
            return "expiring_90_days"
        else:
            return "valid"