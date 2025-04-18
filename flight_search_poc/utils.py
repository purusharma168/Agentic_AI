import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union, Tuple


# Date utilities
def parse_date(date_str: str) -> Union[datetime, None]:
    """
    Parse a date string in various formats

    Args:
        date_str: A string representing a date

    Returns:
        A datetime object if successful, None otherwise
    """
    date_formats = [
        '%d %B %Y',  # 25 December 2025
        '%B %d %Y',  # December 25 2025
        '%d %b %Y',  # 25 Dec 2025
        '%b %d %Y',  # Dec 25 2025
        '%Y-%m-%d',  # 2025-12-25
        '%m/%d/%Y',  # 12/25/2025
        '%d/%m/%Y',  # 25/12/2025
        '%d-%m-%Y',  # 25-12-2025
        '%Y/%m/%d'  # 2025/12/25
    ]

    # Try each format
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    # Try to extract date components if standard formats don't work
    # This handles cases like "4 april 2025" where capitalization or spacing might be irregular
    day, month, year = extract_date_components(date_str)

    if day and month and year:
        try:
            return datetime(year, month, day)
        except ValueError:
            pass

    return None


def extract_date_components(date_str: str) -> Tuple[Union[int, None], Union[int, None], Union[int, None]]:
    """
    Extract day, month, and year from a date string

    Args:
        date_str: A string potentially containing date information

    Returns:
        Tuple of (day, month, year) as integers, or None for components not found
    """
    # Initialize components
    day = None
    month = None
    year = None

    # Convert to lowercase for easier matching
    date_str = date_str.lower()

    # Extract year (4 digits)
    year_match = re.search(r'\b(20\d{2})\b', date_str)
    if year_match:
        year = int(year_match.group(1))

    # Extract day (1 or 2 digits)
    day_match = re.search(r'\b([0-3]?[0-9])(st|nd|rd|th)?\b', date_str)
    if day_match:
        day = int(day_match.group(1))
        if day > 31:  # Invalid day
            day = None

    # Extract month name
    month_names = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }

    for name, num in month_names.items():
        if name in date_str:
            month = num
            break

    # If no month name found, try to extract month number
    if month is None:
        # Check for patterns like MM/DD or DD/MM
        month_match = re.search(r'\b([0-1]?[0-9])[/.-]([0-3]?[0-9])\b', date_str)
        if month_match:
            # Assume Indian format: DD/MM
            m1, m2 = int(month_match.group(1)), int(month_match.group(2))
            if m1 <= 12:
                if day is None and m2 <= 31:
                    # If day wasn't found earlier, use m2 as the day
                    day = m2
                    month = m1
                else:
                    # If day was already found, use m1 as month
                    month = m1

    return day, month, year


def is_past_date(date_obj: datetime) -> bool:
    """
    Check if a date is in the past

    Args:
        date_obj: A datetime object to check

    Returns:
        True if the date is in the past, False otherwise
    """
    current_date = datetime.now().date()
    return date_obj.date() < current_date


def get_next_weekend() -> Tuple[datetime, datetime]:
    """
    Get the dates for the upcoming weekend (Saturday and Sunday)

    Returns:
        Tuple of (saturday, sunday) as datetime objects
    """
    today = datetime.now().date()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:
        days_until_saturday = 7

    next_saturday = datetime.combine(today + timedelta(days=days_until_saturday), datetime.min.time())
    next_sunday = next_saturday + timedelta(days=1)

    return next_saturday, next_sunday


def get_date_range(start_date: datetime, days: int) -> List[datetime]:
    """
    Get a range of dates starting from a specific date

    Args:
        start_date: The starting date
        days: Number of days in the range

    Returns:
        List of datetime objects for each day in the range
    """
    return [start_date + timedelta(days=i) for i in range(days)]


# Text processing utilities
def extract_location_from_text(text: str, locations: List[str]) -> Union[str, None]:
    """
    Extract a location name from text if it matches any in a provided list

    Args:
        text: The text to search
        locations: List of possible location names

    Returns:
        The matched location name or None
    """
    text_lower = text.lower()

    for location in locations:
        if location.lower() in text_lower:
            return location

    return None


def extract_duration_from_text(text: str) -> Union[int, None]:
    """
    Extract trip duration (number of days) from text

    Args:
        text: The text to search

    Returns:
        The number of days or None if not found
    """
    # Look for patterns like "5 days", "a week", "10-day", etc.
    duration_patterns = [
        r'(\d+)\s*days?',
        r'(\d+)\s*\-?\s*days?',
        r'(\d+)\s*night',
        r'(\d+)\s*\-?\s*night'
    ]

    for pattern in duration_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

    # Check for common duration words
    if 'week' in text.lower():
        if 'one week' in text.lower() or '1 week' in text.lower():
            return 7
        elif 'two week' in text.lower() or '2 week' in text.lower():
            return 14
        else:
            return 7  # Default to one week

    if 'weekend' in text.lower():
        return 2  # Weekend trip

    return None  # Duration not found


def extract_interests_from_text(text: str) -> List[str]:
    """
    Extract potential travel interests from text

    Args:
        text: The text to search

    Returns:
        List of identified interests
    """
    common_interests = [
        'adventure', 'trekking', 'hiking', 'nature', 'wildlife', 'beach', 'beaches',
        'shopping', 'food', 'cuisine', 'culinary', 'history', 'historical', 'cultural',
        'culture', 'architecture', 'photography', 'relaxation', 'spa', 'ayurveda',
        'spiritual', 'religious', 'pilgrimage', 'nightlife', 'party', 'family',
        'romantic', 'honeymoon', 'luxury', 'budget', 'backpacking', 'sightseeing'
    ]

    found_interests = []
    text_lower = text.lower()

    for interest in common_interests:
        if interest in text_lower:
            found_interests.append(interest)

    return found_interests


# Flight data processing
def categorize_flight_price(price: float) -> str:
    """
    Categorize a flight price as budget, moderate, or premium

    Args:
        price: The price to categorize (in INR)

    Returns:
        String category: 'Budget', 'Moderate', or 'Premium'
    """
    if price < 3000:
        return 'Budget'
    elif price < 6000:
        return 'Moderate'
    else:
        return 'Premium'


def format_currency_inr(amount: float) -> str:
    """
    Format a number as Indian Rupees

    Args:
        amount: The amount to format

    Returns:
        Formatted string with INR symbol
    """
    return f"₹{amount:,.2f}"


# Itinerary helper functions
def get_popular_destinations() -> List[str]:
    """
    Get a list of popular tourist destinations in India

    Returns:
        List of destination names
    """
    return [
        "Kashmir", "Goa", "Kerala", "Rajasthan", "Himachal Pradesh",
        "Uttarakhand", "Andaman and Nicobar", "Ladakh", "Delhi",
        "Agra", "Jaipur", "Varanasi", "Amritsar", "Rishikesh",
        "Darjeeling", "Ooty", "Munnar", "Coorg", "Hampi", "Puducherry",
        "Mumbai", "Kolkata", "Bangalore", "Chennai", "Hyderabad",
        "Udaipur", "Jaisalmer", "Manali", "Shimla", "Dharamshala",
        "Kovalam", "Alleppey", "Wayanad", "Mysore", "Khajuraho"
    ]


def find_nearest_destination(text: str) -> Union[str, None]:
    """
    Find the nearest match for a destination in a text

    Args:
        text: The text to search

    Returns:
        The matched destination or None
    """
    popular_destinations = get_popular_destinations()
    return extract_location_from_text(text, popular_destinations)
