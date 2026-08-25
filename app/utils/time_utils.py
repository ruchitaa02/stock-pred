from datetime import datetime, timezone, timedelta

# IST Timezone (UTC +5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def current_ist_time() -> datetime:
    """Return current datetime in IST."""
    return datetime.now(IST)

def format_timestamp(dt: datetime = None) -> str:
    """Format datetime to ISO string."""
    if dt is None:
        dt = current_ist_time()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def is_market_hours() -> bool:
    """Check if current time is within NSE market hours (Mon-Fri 09:15 to 15:30 IST)."""
    now = current_ist_time()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_start <= now <= market_end
