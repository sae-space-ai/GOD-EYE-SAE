"""
SAE Core Sources - OpenSky aircraft adapter.

This module implements a source adapter for OpenSky Network aircraft data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

from .contracts import SourceAdapter, SourceStatus
from ..common.enums import generate_id


class OpenSkyAircraftAdapter(SourceAdapter):
    """Adapter for OpenSky Network aircraft data."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize OpenSky adapter."""
        super().__init__("opensky-aircraft", config or {})
        self.base_url = "https://opensky-network.org/api/states/all"
        self.username = config.get("username") if config else None
        self.password = config.get("password") if config else None
    
    def health(self) -> Dict[str, Any]:
        """Check OpenSky API health."""
        try:
            auth = (self.username, self.password) if self.username and self.password else None
            response = requests.get(
                f"{self.base_url}?lamin=40&lomin=-10&lamax=50&lomax=20",
                auth=auth,
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
        Fetch aircraft state vectors from OpenSky.
        
        Args:
            params: Query parameters (lamin, lomin, lamax, lomax, etc.)
        
        Returns:
            List of aircraft state vectors
        """
        params = params or {}
        
        auth = (self.username, self.password) if self.username and self.password else None
        
        try:
            response = requests.get(self.base_url, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            aircraft_list = []
            
            states = data.get("states", [])
            for state in states:
                # OpenSky state vector format:
                # [icao24, callsign, origin_country, time_position, last_contact,
                #  longitude, latitude, baro_altitude, on_ground, velocity,
                #  true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
                
                if len(state) < 17:
                    continue
                
                icao24 = state[0]
                callsign = state[1]
                origin_country = state[2]
                time_position = state[3]
                last_contact = state[4]
                longitude = state[5]
                latitude = state[6]
                baro_altitude = state[7]
                on_ground = state[8]
                velocity = state[9]
                true_track = state[10]
                vertical_rate = state[11]
                # sensors = state[12]
                geo_altitude = state[13]
                squawk = state[14]
                spi = state[15]
                position_source = state[16]
                
                # Skip if no position
                if longitude is None or latitude is None:
                    continue
                
                aircraft = {
                    "id": icao24 or generate_id(),
                    "type": "aircraft",
                    "icao24": icao24,
                    "callsign": callsign.strip() if callsign else None,
                    "origin_country": origin_country,
                    "time_position": time_position,
                    "last_contact": last_contact,
                    "on_ground": on_ground,
                    "velocity": velocity,
                    "true_track": true_track,
                    "vertical_rate": vertical_rate,
                    "squawk": squawk,
                    "spi": spi,
                    "position_source": position_source,
                    "geometry": {
                        "type": "Point",
                        "coordinates": {
                            "longitude": longitude,
                            "latitude": latitude,
                            "altitude": geo_altitude if geo_altitude is not None else baro_altitude
                        }
                    },
                    "provenance": {
                        "source_id": self.source_id,
                        "source_name": "OpenSky Network",
                        "source_url": f"https://opensky-network.org/aircraft/{icao24}",
                        "retrieved_at": datetime.utcnow().isoformat()
                    }
                }
                aircraft_list.append(aircraft)
            
            return aircraft_list
        
        except Exception as e:
            raise RuntimeError(f"Failed to fetch OpenSky data: {e}")
    
    def normalize(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize aircraft data to standard format.
        
        Args:
            raw_data: Raw aircraft data from fetch_data
        
        Returns:
            Normalized aircraft records
        """
        # Data is already normalized in fetch_data
        return raw_data
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get source metadata."""
        return {
            "id": self.source_id,
            "name": "OpenSky Network",
            "category": "aircraft",
            "provider": "OpenSky Network",
            "url": "https://opensky-network.org",
            "license": "OpenSky Terms of Use",
            "update_frequency": "real-time",
            "capabilities": [
                "aircraft_tracking",
                "position_data",
                "velocity_data",
                "altitude_data"
            ],
            "authentication_required": self.username is not None
        }
