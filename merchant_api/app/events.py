from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    ANOMALY_DETECTED = "anomaly_detected"
    RISK_ALERT = "risk_alert"
    MERCHANT_STATUS_CHANGE = "merchant_status_change"
    TRANSACTION_PATTERN = "transaction_pattern"
    SYSTEM_ALERT = "system_alert"

class EventPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EventProcessor:
    def __init__(self):
        self.events: List[Dict] = []
        self.handlers: Dict = {}

    def register_handler(self, event_type: EventType, handler):
        """Register a handler for a specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def process_event(self, event_type: EventType, data: Dict, priority: EventPriority = EventPriority.MEDIUM):
        """Process a new event"""
        event = {
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            "priority": priority.value,
            "data": data
        }
        
        self.events.append(event)
        
        # Call registered handlers
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {str(e)}")

        return event

    def get_events(self, 
                  event_type: Optional[EventType] = None, 
                  priority: Optional[EventPriority] = None,
                  limit: int = 100) -> List[Dict]:
        """Get filtered events"""
        filtered_events = self.events
        
        if event_type:
            filtered_events = [e for e in filtered_events if e["type"] == event_type.value]
        
        if priority:
            filtered_events = [e for e in filtered_events if e["priority"] == priority.value]
        
        return sorted(filtered_events, 
                     key=lambda x: x["timestamp"], 
                     reverse=True)[:limit]

# Create global event processor instance
event_processor = EventProcessor() 