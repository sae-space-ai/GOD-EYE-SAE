"""
SAE Core Sources - CelesTrak satellite adapter.

This module implements a source adapter for CelesTrak satellite TLE data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

from .contracts import SourceAdapter, SourceStatus
from ..common.enums import generate_id


class CelesTrakSatelliteAdapter(SourceAdapter):
    """Adapter for CelesTrak satellite TLE data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CelesTrak adapter."""
        super().__init__("celestrak-satellites", config or {})
        self.base_url = "https://celestrak.org/NORAD/elements/gp.php"
    
    def health(self) -> Dict[str, Any]:
        """Check CelesTrak API health."""
        try:
            response = requests.get(
                f"{self.base_url}?GROUP=active&FORMAT=json&FORMAT=json",
                timeout=10
            )
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "latency_ms": response.elapsed.total_seconds() * 1000,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def fetch_data(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch satellite TLE data from CelesTrak.
        
        Args:
            params: Query parameters (GROUP, LIMIT, etc.)
        
        Returns:
            List of satellite records with TLE
        """
        params = params or {}
        
        # Default to active satellites
        if "GROUP" not in params:
            params["GROUP"] = "active"
        if "FORMAT" not in params:
            params["FORMAT"] = "json"
        if "LIMIT" not in params:
            params["LIMIT"] = 100
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            satellites = []
            
            for sat_data in data:
                satellite = {
                    "id": sat_data.get("OBJECT_ID", generate_id()),
                    "type": "satellite",
                    "name": sat_data.get("OBJECT_NAME"),
                    "norad_id": sat_data.get("NORAD_CAT_ID"),
                    "classification": sat_data.get("CLASSIFICATION_TYPE"),
                    "intl_designator": sat_data.get("INTLDES"),
                    "epoch": sat_data.get("EPOCH"),
                    "mean_motion": sat_data.get("MEAN_MOTION"),
                    "eccentricity": sat_data.get("ECCENTRICITY"),
                    "inclination": sat_data.get("INCLINATION"),
                    "ra_of_asc_node": sat_data.get("RA_OF_ASC_NODE"),
                    "arg_of_pericenter": sat_data.get("ARG_OF_PERICENTER"),
                    "mean_anomaly": sat_data.get("MEAN_ANOMALY"),
                    "rev_number": sat_data.get("REV_NUMBER"),
                    "tle_line1": sat_data.get("TLE_LINE1"),
                    "tle_line2": sat_data.get("TLE_LINE2"),
                    "provenance": {
                        "source_id": self.source_id,
                        "source_name": "CelesTrak",
                        "source_url": f"https://celestrak.org/NORAD/elements/gp.php?GROUP={params['GROUP']}",
                        "retrieved_at": datetime.utcnow().isoformat()
                    }
                }
                satellites.append(satellite)
            
            return satellites
        
        except Exception as e:
            raise RuntimeError(f"Failed to fetch CelesTrak data: {e}")
    
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize satellite data to standard format.
        
        Args:
            raw_data: Raw satellite data from fetch_data
        
        Returns:
            Normalized satellite records
        """
        # Data is already normalized in fetch_data
        return raw_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get source metadata."""
        return {
            "id": self.source_id,
            "name": "CelesTrak",
            "category": "satellites",
            "provider": "CelesTrak",
            "url": "https://celestrak.org",
            "license": "Public Domain",
            "update_frequency": "daily",
            "capabilities": [
                "tle_data",
                "orbital_elements",
                "satellite_tracking",
                "pass_prediction"
            ]
        }
