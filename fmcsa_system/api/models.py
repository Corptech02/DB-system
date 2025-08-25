"""
Pydantic models for FMCSA Database Management System.
Defines data structures for carriers, search filters, and API responses.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Literal
from decimal import Decimal
from uuid import UUID
from enum import Enum


class OperatingStatus(str, Enum):
    """Carrier operating status enumeration."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    AUTHORIZED_FOR_PROPERTY = "AUTHORIZED_FOR_PROPERTY"
    AUTHORIZED_FOR_HHG = "AUTHORIZED_FOR_HHG"


class EntityType(str, Enum):
    """Carrier entity type enumeration."""
    CARRIER = "CARRIER"
    BROKER = "BROKER"
    FREIGHT_FORWARDER = "FREIGHT_FORWARDER"
    SHIPPER = "SHIPPER"
    REGISTRANT = "REGISTRANT"
    CARGO_TANK = "CARGO_TANK"


class SafetyRating(str, Enum):
    """Safety rating enumeration."""
    SATISFACTORY = "SATISFACTORY"
    CONDITIONAL = "CONDITIONAL"
    UNSATISFACTORY = "UNSATISFACTORY"
    UNRATED = "UNRATED"


class InsuranceStatus(str, Enum):
    """Insurance status enumeration."""
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"
    EXPIRING_60_DAYS = "expiring_60_days"
    EXPIRING_90_DAYS = "expiring_90_days"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class CarrierBase(BaseModel):
    """Base carrier model with FMCSA fields."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    
    usdot_number: int = Field(..., description="USDOT Number", gt=0)
    legal_name: str = Field(..., min_length=1, max_length=255, description="Legal company name")
    dba_name: Optional[str] = Field(None, max_length=255, description="Doing Business As name")
    
    # Address information
    physical_address: Optional[str] = Field(None, max_length=500)
    physical_city: Optional[str] = Field(None, max_length=100)
    physical_state: Optional[str] = Field(None, max_length=2, pattern="^[A-Z]{2}$")
    physical_zip: Optional[str] = Field(None, max_length=10, pattern="^\\d{5}(-\\d{4})?$")
    physical_country: Optional[str] = Field(default="US", max_length=2)
    
    mailing_address: Optional[str] = Field(None, max_length=500)
    mailing_city: Optional[str] = Field(None, max_length=100)
    mailing_state: Optional[str] = Field(None, max_length=2, pattern="^[A-Z]{2}$")
    mailing_zip: Optional[str] = Field(None, max_length=10, pattern="^\\d{5}(-\\d{4})?$")
    
    # Contact information
    telephone: Optional[str] = Field(None, max_length=20, pattern="^[\\d\\s\\-\\(\\)\\+]+$")
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255, pattern="^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$")
    
    # Carrier details
    mcs_150_date: Optional[date] = Field(None, description="MCS-150 form date")
    mcs_150_mileage: Optional[int] = Field(None, ge=0)
    entity_type: Optional[str] = Field(None, max_length=50)
    operating_status: Optional[str] = Field(None, max_length=50)
    out_of_service_date: Optional[date] = None
    
    # Operations
    power_units: Optional[int] = Field(None, ge=0, description="Number of power units")
    drivers: Optional[int] = Field(None, ge=0, description="Number of drivers")
    carrier_operation: Optional[str] = Field(None, max_length=100)
    cargo_carried: Optional[List[str]] = Field(default_factory=list)
    
    # Insurance
    liability_insurance_date: Optional[date] = Field(None, description="Liability insurance expiration")
    liability_insurance_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    cargo_insurance_date: Optional[date] = None
    cargo_insurance_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    bond_insurance_date: Optional[date] = None
    bond_insurance_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    
    # Hazmat
    hazmat_flag: bool = Field(default=False, description="Hazmat authorization")
    hazmat_placardable: bool = Field(default=False)
    
    # Safety
    safety_rating: Optional[str] = None
    safety_rating_date: Optional[date] = None
    safety_review_date: Optional[date] = None
    
    @field_validator('physical_state', 'mailing_state', mode='before')
    @classmethod
    def uppercase_state(cls, v: Optional[str]) -> Optional[str]:
        """Convert state codes to uppercase."""
        return v.upper() if v else None
    
    @field_validator('email', mode='before')
    @classmethod
    def lowercase_email(cls, v: Optional[str]) -> Optional[str]:
        """Convert email to lowercase."""
        return v.lower() if v else None


class CarrierCreate(CarrierBase):
    """Model for creating carrier from FMCSA data."""
    raw_data: Dict[str, Any] = Field(..., description="Complete FMCSA record")
    
    @classmethod
    def from_fmcsa_record(cls, record: Dict[str, Any]) -> 'CarrierCreate':
        """
        Create carrier from FMCSA API record.
        Maps FMCSA field names to our schema.
        """
        # Map FMCSA fields to our model fields
        mapped_data = {
            'usdot_number': int(record.get('usdot_number', 0)),
            'legal_name': record.get('legal_name', ''),
            'dba_name': record.get('dba_name'),
            'physical_address': record.get('phy_street'),
            'physical_city': record.get('phy_city'),
            'physical_state': record.get('phy_state'),
            'physical_zip': record.get('phy_zip'),
            'physical_country': record.get('phy_country', 'US'),
            'mailing_address': record.get('mailing_street'),
            'mailing_city': record.get('mailing_city'),
            'mailing_state': record.get('mailing_state'),
            'mailing_zip': record.get('mailing_zip'),
            'telephone': record.get('telephone'),
            'fax': record.get('fax'),
            'email': record.get('email_address'),
            'entity_type': record.get('entity_type'),
            'operating_status': record.get('operating_status'),
            'power_units': int(record.get('power_units', 0)) if record.get('power_units') else None,
            'drivers': int(record.get('drivers', 0)) if record.get('drivers') else None,
            'raw_data': record
        }
        
        # Parse dates
        if record.get('mcs_150_date'):
            try:
                mapped_data['mcs_150_date'] = datetime.strptime(
                    record['mcs_150_date'], 
                    '%Y-%m-%dT%H:%M:%S.%f'
                ).date()
            except:
                pass
        
        # Add more field mappings as needed
        
        return cls(**mapped_data)


class CarrierResponse(CarrierBase):
    """Response model with calculated fields."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    days_until_insurance_expiration: Optional[int] = None
    insurance_status: Optional[InsuranceStatus] = None
    
    @model_validator(mode='after')
    def calculate_insurance_status(self) -> 'CarrierResponse':
        """Calculate insurance status and days until expiration."""
        if not self.liability_insurance_date:
            self.insurance_status = InsuranceStatus.UNKNOWN
            self.days_until_insurance_expiration = None
        else:
            days = (self.liability_insurance_date - date.today()).days
            self.days_until_insurance_expiration = days
            
            if days < 0:
                self.insurance_status = InsuranceStatus.EXPIRED
            elif days <= 30:
                self.insurance_status = InsuranceStatus.EXPIRING_SOON
            elif days <= 60:
                self.insurance_status = InsuranceStatus.EXPIRING_60_DAYS
            elif days <= 90:
                self.insurance_status = InsuranceStatus.EXPIRING_90_DAYS
            else:
                self.insurance_status = InsuranceStatus.VALID
        
        return self


class CarrierSummary(BaseModel):
    """Simplified carrier model for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    usdot_number: int
    legal_name: str
    dba_name: Optional[str] = None
    physical_state: Optional[str] = None
    physical_city: Optional[str] = None
    operating_status: Optional[str] = None
    entity_type: Optional[str] = None
    insurance_status: Optional[InsuranceStatus] = None
    days_until_insurance_expiration: Optional[int] = None


class SearchFilters(BaseModel):
    """Search query parameters."""
    # Direct search fields
    usdot_number: Optional[int] = Field(None, gt=0)
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    state: Optional[str] = Field(None, max_length=2, pattern="^[A-Z]{2}$")
    city: Optional[str] = Field(None, max_length=100)
    
    # Filter fields
    entity_type: Optional[EntityType] = None
    operating_status: Optional[OperatingStatus] = None
    safety_rating: Optional[SafetyRating] = None
    
    # Insurance filters
    insurance_status: Optional[InsuranceStatus] = None
    insurance_expiring_days: Optional[int] = Field(None, ge=0, le=365)
    
    # Hazmat filter
    hazmat_only: bool = Field(default=False)
    
    # Range filters
    min_power_units: Optional[int] = Field(None, ge=0)
    max_power_units: Optional[int] = Field(None, ge=0)
    min_drivers: Optional[int] = Field(None, ge=0)
    max_drivers: Optional[int] = Field(None, ge=0)
    
    # Pagination
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    
    # Sorting
    sort_by: Literal['legal_name', 'usdot_number', 'state', 'insurance_date', 'created_at'] = 'legal_name'
    sort_order: Literal['asc', 'desc'] = 'asc'
    
    @field_validator('state', mode='before')
    @classmethod
    def uppercase_state(cls, v: Optional[str]) -> Optional[str]:
        """Convert state code to uppercase."""
        return v.upper() if v else None
    
    @model_validator(mode='after')
    def validate_ranges(self) -> 'SearchFilters':
        """Validate range filters."""
        if self.min_power_units and self.max_power_units:
            if self.min_power_units > self.max_power_units:
                raise ValueError("min_power_units cannot be greater than max_power_units")
        
        if self.min_drivers and self.max_drivers:
            if self.min_drivers > self.max_drivers:
                raise ValueError("min_drivers cannot be greater than max_drivers")
        
        return self


class ExportRequest(BaseModel):
    """Export request parameters."""
    filters: SearchFilters = Field(..., description="Search filters to apply")
    format: Literal['csv', 'xlsx'] = Field('csv', description="Export format")
    columns: Optional[List[str]] = Field(None, description="Specific columns to export")
    include_raw_data: bool = Field(default=False, description="Include raw FMCSA data")
    
    @field_validator('columns')
    @classmethod
    def validate_columns(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate requested columns exist."""
        if v:
            allowed_columns = {
                'usdot_number', 'legal_name', 'dba_name',
                'physical_address', 'physical_city', 'physical_state', 'physical_zip',
                'telephone', 'email', 'entity_type', 'operating_status',
                'power_units', 'drivers', 'liability_insurance_date',
                'insurance_status', 'days_until_insurance_expiration'
            }
            invalid = set(v) - allowed_columns
            if invalid:
                raise ValueError(f"Invalid columns: {invalid}")
        return v


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    model_config = ConfigDict(extra='forbid')
    
    data: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool
    
    @model_validator(mode='after')
    def calculate_has_more(self) -> 'PaginatedResponse':
        """Calculate if there are more results."""
        self.has_more = (self.offset + self.limit) < self.total
        return self


class ExportResponse(BaseModel):
    """Export response with download information."""
    file_id: str
    filename: str
    format: str
    size_bytes: int
    row_count: int
    download_url: str
    expires_at: datetime


class StatisticsResponse(BaseModel):
    """Carrier statistics response."""
    total_carriers: int
    active_carriers: int
    inactive_carriers: int
    
    by_state: Dict[str, int]
    by_entity_type: Dict[str, int]
    by_operating_status: Dict[str, int]
    
    insurance_stats: Dict[str, int]
    hazmat_carriers: int
    
    avg_power_units: float
    avg_drivers: float
    
    last_updated: datetime


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: Literal['healthy', 'degraded', 'unhealthy']
    database: bool
    last_ingestion: Optional[datetime]
    carrier_count: Optional[int]
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)