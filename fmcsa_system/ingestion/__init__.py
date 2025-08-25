"""
FMCSA data ingestion module.
Handles fetching data from FMCSA API and storing in PostgreSQL.
"""

from .fmcsa_client import FMCSAClient
from .ingestion_pipeline import (
    IngestionPipeline,
    IngestionStats,
    CarrierDataNormalizer
)

__all__ = [
    'FMCSAClient',
    'IngestionPipeline',
    'IngestionStats',
    'CarrierDataNormalizer'
]