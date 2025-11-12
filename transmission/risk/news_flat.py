"""
News Flat Module

Avoids trading during high-impact news windows.
Loads economic calendar and enforces blackout intervals.
"""

from typing import Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import yaml
from pathlib import Path

from transmission.config.config_loader import ConfigLoader


@dataclass
class NewsEvent:
    """Economic calendar event"""
    symbol: Optional[str]  # None for market-wide events
    event_name: str
    timestamp: datetime
    impact: Literal["HIGH", "MEDIUM", "LOW"]
    blackout_before_minutes: int
    blackout_after_minutes: int


class NewsFlat:
    """
    News flat module.
    
    Loads economic calendar and enforces blackout periods.
    Rejects entries X minutes before/after high-impact events.
    """
    
    def __init__(self, calendar_path: Optional[str] = None):
        """
        Initialize News Flat.
        
        Args:
            calendar_path: Path to news calendar YAML (defaults to config)
        """
        if calendar_path is None:
            config_dir = Path(__file__).parent.parent / "config"
            calendar_path = config_dir / "news_calendar.yaml"
        
        self.calendar_path = Path(calendar_path)
        self.events: List[NewsEvent] = []
        self.last_load_time: Optional[datetime] = None
        self.enabled: bool = True
        
        self.load_calendar()
    
    def load_calendar(self) -> None:
        """Load news calendar from YAML file"""
        try:
            if not self.calendar_path.exists():
                logger.warning(f"News calendar not found: {self.calendar_path}")
                self.events = []
                return
            
            with open(self.calendar_path, 'r') as f:
                data = yaml.safe_load(f)
            
            self.events = []
            
            # Parse events
            calendar = data.get('calendar', {})
            for event_data in calendar.get('events', []):
                try:
                    event = NewsEvent(
                        symbol=event_data.get('symbol'),
                        event_name=event_data.get('name', 'Unknown'),
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        impact=event_data.get('impact', 'MEDIUM'),
                        blackout_before_minutes=event_data.get('blackout_before', 30),
                        blackout_after_minutes=event_data.get('blackout_after', 30)
                    )
                    self.events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
            
            self.last_load_time = datetime.now()
            logger.info(f"Loaded {len(self.events)} news events from calendar")
            
        except Exception as e:
            logger.error(f"Failed to load news calendar: {e}")
            self.events = []
    
    def reload_calendar(self) -> None:
        """Hot-reload calendar (for runtime updates)"""
        self.load_calendar()
        logger.info("News calendar reloaded")
    
    def check_blackout(
        self,
        symbol: Optional[str] = None,
        current_time: Optional[datetime] = None,
        min_impact: Literal["HIGH", "MEDIUM", "LOW"] = "HIGH"
    ) -> tuple[bool, Optional[str]]:
        """
        Check if we're in a news blackout period.
        
        Args:
            symbol: Trading symbol (None for market-wide)
            current_time: Current time (defaults to now)
            min_impact: Minimum impact level to check
        
        Returns:
            Tuple of (in_blackout: bool, reason: Optional[str])
        """
        if not self.enabled:
            return False, None
        
        if current_time is None:
            current_time = datetime.now()
        
        # Reload calendar if stale (every hour)
        if self.last_load_time is None or \
           (current_time - self.last_load_time) > timedelta(hours=1):
            self.load_calendar()
        
        # Check each event
        for event in self.events:
            # Filter by impact
            impact_levels = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
            if impact_levels.get(event.impact, 0) < impact_levels.get(min_impact, 0):
                continue
            
            # Filter by symbol (if specified)
            if symbol and event.symbol and event.symbol != symbol:
                continue
            
            # Check if we're in blackout window
            blackout_start = event.timestamp - timedelta(minutes=event.blackout_before_minutes)
            blackout_end = event.timestamp + timedelta(minutes=event.blackout_after_minutes)
            
            if blackout_start <= current_time <= blackout_end:
                reason = (
                    f"News blackout: {event.event_name} "
                    f"({event.impact} impact) "
                    f"at {event.timestamp.strftime('%H:%M')}"
                )
                return True, reason
        
        return False, None
    
    def get_upcoming_events(
        self,
        symbol: Optional[str] = None,
        hours_ahead: int = 24
    ) -> List[NewsEvent]:
        """
        Get upcoming news events.
        
        Args:
            symbol: Filter by symbol
            hours_ahead: How many hours ahead to look
        
        Returns:
            List of upcoming events
        """
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)
        
        upcoming = []
        for event in self.events:
            if event.timestamp > now and event.timestamp <= cutoff:
                if symbol is None or event.symbol is None or event.symbol == symbol:
                    upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.timestamp)
    
    def enable(self) -> None:
        """Enable news flat module"""
        self.enabled = True
        logger.info("News flat module enabled")
    
    def disable(self) -> None:
        """Disable news flat module"""
        self.enabled = False
        logger.info("News flat module disabled")

