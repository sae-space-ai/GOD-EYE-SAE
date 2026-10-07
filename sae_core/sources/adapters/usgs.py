"""
SAE Core Sources - USGS Earthquake adapter.

This module implements a source adapter for USGS earthquake data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

from .contracts import SourceAdapter, SourceStatus
from ..common.enums import generate_id


class USGSEarthquakeAdapter(SourceAdapter):
    """Adapter for USGS Earthquake Hazards Program."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize USGS adapter."""
        super().__init__("usgs-earthquakes", config or {})
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def health(self) -> Dict[str, Any]:
        """Check USGS API health."""
        try:
            response = requests.get(
                f"{self.base_url}?format=geojson&limit=1",
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
        Fetch earthquake data from USGS.
        
        Args:
            params: Query parameters (starttime, endtime, minmagnitude, etc.)
        
        Returns:
            List of earthquake records
        """
        params = params or {}
        
        # Default to last 24 hours, magnitude 2.5+
        if "starttime" not in params:
            params["starttime"] = (datetime.utcnow().replace(hour=0, minute=0, second=0)).isoformat()
        if "endtime" not in params:
            params["endtime"] = datetime.utcnow().isoformat()
        if "minmagnitude" not in params:
            params["minmagnitude"] = 2.5
        
        params["format"] = "geojson"
        params["limit"] = params.get("limit", 1000)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            earthquakes = []
            
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                geom = feature.get("geometry", {})
                coords = geom.get("coordinates", [0, 0, 0])
                
                earthquake = {
                    "id": feature.get("id", generate_id()),
                    "type": "earthquake",
                    "magnitude": props.get("mag"),
                    "place": props.get("place"),
                    "time": props.get("time"),
                    "updated": props.get("updated"),
                    "timezone": props.get("tz"),
                    "url": props.get("url"),
                    "detail": props.get("detail"),
                    "felt": props.get("felt"),
                    "alert": props.get("alert"),
                    "status": props.get("status"),
                    "tsunami": props.get("tsunami"),
                    "sig": props.get("sig"),
                    "net": props.get("net"),
                    "code": props.get("code"),
                    "ids": props.get("ids"),
                    "sources": props.get("sources"),
                    "types": props.get("types"),
                    "nst": props.get("nst"),
                    "dmin": props.get("dmin"),
                    "rms": props.get("rms"),
                    "gap": props.get("gap"),
                    "magType": props.get("magType"),
                    "type": props.get("type"),
                    "geometry": {
                        "type": "Point",
                        "coordinates": {
                            "longitude": coords[0],
                            "latitude": coords[1],
                            "depth": coords[2] if len(coords) > 2 else 0
                        }
                    },
                    "provenance": {
                        "source_id": self.source_id,
                        "source_name": "USGS Earthquake Hazards Program",
                        "source_url": props.get("url"),
                        "retrieved_at": datetime.utcnow().isoformat()
                    }
                }
                earthquakes.append(earthquake)
            
            return earthquakes
        
        except Exception as e:
            raise RuntimeError(f"Failed to fetch USGS data: {e}")
    
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize earthquake data to standard format.
        
        Args:
            raw_data: Raw earthquake data from fetch_data
        
        Returns:
            Normalized earthquake records
        """
        # Data is already normalized in fetch_data
        return raw_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get source metadata."""
        return {
            "id": self.source_id,
            "name": "USGS Earthquake Hazards Program",
            "category": "earthquakes",
            "provider": "USGS",
            "url": "https://earthquake.usgs.gov",
            "license": "Public Domain",
            "update_frequency": "real-time",
            "capabilities": [
                "earthquake_detection",
                "magnitude_reporting",
                "location_data",
                "depth_data"
            ]
        }
