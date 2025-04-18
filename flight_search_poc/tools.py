import os
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple, Union
from datetime import datetime, timedelta
import random


# Web search for flight information with focus on Indian context
def web_search_flights(query: str) -> str:
    """
    Search the web for flight information based on the query

    Args:
        query: The search query for flight information

    Returns:
        Text results from the web search
    """
    try:
        # Check if the query is for past dates
        past_date = is_past_date(query)
        if past_date:
            return f"I'm sorry, but the date in your query ({past_date}) appears to be in the past. Flight bookings can only be made for future dates. Please provide a future date for your travel plans."

        # Add Indian context if not already present
        if not any(city in query.lower() for city in
                   ["delhi", "mumbai", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad", "jaipur",
                    "lucknow", "kochi", "goa"]):
            # Don't add India context if it seems to be an international query
            if not any(intl in query.lower() for intl in ["international", "london", "new york", "dubai", "singapore"]):
                query = f"India {query}"

        # Format query for better flight search results
        if "flight" not in query.lower():
            query = f"flight {query}"

        # Use Google Search API or equivalent
        search_api_key = os.environ.get("SERPER_API_KEY", "YOUR_SERPER_API_KEY")
        headers = {
            'X-API-KEY': search_api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': 5  # Get top 5 results
        }

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)

        if response.status_code != 200:
            return f"Error searching for flight information: HTTP {response.status_code}"

        search_results = response.json()

        # Extract organic search results
        organic_results = search_results.get('organic', [])

        if not organic_results:
            return "No flight information found. Please try a more specific query."

        # Compile relevant search results
        compiled_results = f"Web search results for flight information regarding: {query}\n\n"

        for i, result in enumerate(organic_results, 1):
            title = result.get('title', 'No title')
            link = result.get('link', 'No link')
            snippet = result.get('snippet', 'No description')

            compiled_results += f"Result {i}:\n"
            compiled_results += f"Title: {title}\n"
            compiled_results += f"Description: {snippet}\n"
            compiled_results += f"URL: {link}\n\n"

        # Now, try to get more detailed information from the first result
        if organic_results and 'link' in organic_results[0]:
            top_link = organic_results[0]['link']
            try:
                page_response = requests.get(top_link, timeout=5)
                if page_response.status_code == 200:
                    soup = BeautifulSoup(page_response.content, 'html.parser')

                    # Extract main content text
                    main_text = soup.get_text(separator=' ', strip=True)

                    # Truncate to a reasonable size
                    main_text = main_text[:5000] + "..." if len(main_text) > 5000 else main_text

                    compiled_results += "Detailed information from top result:\n"
                    compiled_results += main_text + "\n\n"
            except Exception as e:
                compiled_results += f"Could not fetch detailed information: {str(e)}\n\n"

        return compiled_results

    except Exception as e:
        return f"Error searching for flight information: {str(e)}"


# Flight information extraction with focus on Indian flights
def extract_flight_info(date_str: str, origin: str, destination: str) -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Search for specific flight information for a given date, origin, and destination

    Args:
        date_str: The date to search flights for
        origin: The departure city or airport code
        destination: The arrival city or airport code

    Returns:
        A tuple containing (response_text, data_type, flight_data)
    """
    try:
        # Parse and validate the date
        try:
            # Try different date formats
            date_formats = ['%d %B %Y', '%B %d %Y', '%d %b %Y', '%b %d %Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']

            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue

            if not parsed_date:
                # Try to handle "4 april 2025" format
                parts = date_str.split()
                if len(parts) >= 2:
                    day = parts[0] if parts[0].isdigit() else None
                    month = None
                    year = None

                    for part in parts:
                        if part.lower() in ['january', 'february', 'march', 'april', 'may', 'june',
                                            'july', 'august', 'september', 'october', 'november', 'december',
                                            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
                                            'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
                            month = part
                        elif len(part) == 4 and part.isdigit():
                            year = part

                    if day and month and year:
                        date_str = f"{day} {month} {year}"
                        for fmt in date_formats:
                            try:
                                parsed_date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue

            if not parsed_date:
                # Use current date + 7 days if parsing fails
                parsed_date = datetime.now() + timedelta(days=7)

            # Check if date is in the past
            if parsed_date.date() < datetime.now().date():
                return "I'm sorry, but you've selected a date in the past. Please choose a future date for your flight search.", "error", []

            formatted_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            # Use current date + 7 days if parsing fails
            future_date = datetime.now() + timedelta(days=7)
            formatted_date = future_date.strftime("%Y-%m-%d")

        # Map common Indian cities to airport codes if needed
        origin = map_indian_city_to_airport(origin)
        destination = map_indian_city_to_airport(destination)

        # Generate realistic flight data for Indian context
        flight_data = generate_indian_flight_data(formatted_date, origin, destination)

        # Format the response with detailed flight information
        response = f"Flight information for {date_str} from {origin} to {destination}:\n\n"

        for i, flight in enumerate(flight_data, 1):
            response += f"Flight {i}: {flight['airline']} {flight['flight_number']}\n"
            response += f"Route: {flight['origin']} to {flight['destination']}\n"
            response += f"Date: {flight['departure_date']}\n"
            response += f"Departure: {flight['departure_time']} from {flight['origin']}\n"
            response += f"Arrival: {flight['arrival_time']} at {flight['destination']}\n"
            response += f"Duration: {flight['duration']}\n"
            response += f"Stops: {flight['stops']}\n"
            response += f"Price: ₹{flight['price']}\n"
            response += f"Seats available: {flight['seats_available']}\n\n"

        return response, "flight", flight_data

    except Exception as e:
        return f"Error retrieving flight information: {str(e)}", "error", []


# Function to generate itinerary plans
def plan_itinerary(destination: str, duration: int, interests: str = "") -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Create a detailed travel itinerary for a destination

    Args:
        destination: The destination for the itinerary
        duration: Number of days for the trip
        interests: Optional comma-separated list of traveler's interests

    Returns:
        A tuple containing (response_text, data_type, itinerary_data)
    """
    try:
        # Normalize destination
        destination = destination.strip().title()

        # Parse interests if provided
        interest_list = []
        if interests:
            interest_list = [i.strip().lower() for i in interests.split(",")]

        # Web search for destination information (simplified for the demo)
        destination_info = get_destination_info(destination)

        # Generate detailed itinerary
        itinerary_data = generate_itinerary(destination, duration, destination_info, interest_list)

        # Format the response
        response = f"Travel Itinerary for {destination} - {duration} days\n\n"

        for i, day in enumerate(itinerary_data, 1):
            response += f"Day {i}: {day['title']}\n"
            response += f"Morning: {day['morning']}\n"
            response += f"Afternoon: {day['afternoon']}\n"
            response += f"Evening: {day['evening']}\n"

            if 'accommodation' in day:
                response += f"Accommodation: {day['accommodation']}\n"

            if 'notes' in day:
                response += f"Notes: {day['notes']}\n"

            response += "\n"

        response += "This itinerary is customized based on your interests and the destination's highlights. You can adjust the activities based on your preferences and travel pace."

        return response, "itinerary", itinerary_data

    except Exception as e:
        return f"Error creating itinerary: {str(e)}", "error", []


# Helper Functions

def is_past_date(query: str) -> Union[str, None]:
    """Check if the query contains a past date"""
    date_patterns = [
        r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[,\s]+(\d{4})',
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})'
    ]

    current_date = datetime.now().date()

    for pattern in date_patterns:
        import re
        matches = re.findall(pattern, query, re.IGNORECASE)

        if matches:
            for match in matches:
                try:
                    if len(match) == 3:
                        if pattern == date_patterns[0]:  # dd Month yyyy
                            day, month, year = match
                            month_num = datetime.strptime(month, '%B').month
                        elif pattern == date_patterns[1]:  # Month dd, yyyy
                            month, day, year = match
                            month_num = datetime.strptime(month, '%B').month
                        elif pattern == date_patterns[2]:  # dd/mm/yyyy or mm/dd/yyyy
                            # Assume Indian format dd/mm/yyyy
                            day, month_num, year = match
                        else:  # yyyy/mm/dd
                            year, month_num, day = match

                        date_obj = datetime(int(year), int(month_num), int(day)).date()

                        if date_obj < current_date:
                            return f"{day} {month if 'month' in locals() else month_num} {year}"
                except:
                    continue

    return None


def map_indian_city_to_airport(city: str) -> str:
    """Map common Indian cities to their airport codes"""
    city_to_code = {
        "delhi": "DEL",
        "new delhi": "DEL",
        "mumbai": "BOM",
        "bangalore": "BLR",
        "bengaluru": "BLR",
        "hyderabad": "HYD",
        "chennai": "MAA",
        "kolkata": "CCU",
        "ahmedabad": "AMD",
        "pune": "PNQ",
        "jaipur": "JAI",
        "goa": "GOI",
        "lucknow": "LKO",
        "kochi": "COK",
        "cochin": "COK",
        "thiruvananthapuram": "TRV",
        "trivandrum": "TRV",
        "bhubaneswar": "BBI",
        "indore": "IDR",
        "nagpur": "NAG",
        "patna": "PAT",
        "chandigarh": "IXC",
        "srinagar": "SXR",
        "kashmir": "SXR"
    }

    # If already an airport code (3 uppercase letters), return as is
    if len(city) == 3 and city.isupper():
        return city

    # Otherwise, try to map the city name
    normalized_city = city.lower().strip()

    # Check for exact match
    if normalized_city in city_to_code:
        return city_to_code[normalized_city]

    # Check for partial match
    for city_name, code in city_to_code.items():
        if city_name in normalized_city or normalized_city in city_name:
            return code

    # If no match found, return the original input
    return city


def generate_indian_flight_data(date_str: str, origin: str, destination: str) -> List[Dict[str, Any]]:
    """Generate realistic flight data for Indian routes"""
    flight_data = []

    # List of Indian airlines
    airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "Air Asia India", "Go Air", "Alliance Air"]

    # Number of flights to generate (random between 5-10)
    num_flights = random.randint(5, 10)

    for i in range(num_flights):
        # Select airline
        airline = airlines[i % len(airlines)]

        # Generate flight number
        if airline == "Air India":
            flight_number = f"AI{100 + i}"
        elif airline == "IndiGo":
            flight_number = f"6E{100 + i * 10}"
        elif airline == "SpiceJet":
            flight_number = f"SG{100 + i * 5}"
        elif airline == "Vistara":
            flight_number = f"UK{100 + i * 8}"
        elif airline == "Air Asia India":
            flight_number = f"I5{100 + i * 7}"
        elif airline == "Go Air":
            flight_number = f"G8{100 + i * 6}"
        else:
            flight_number = f"9I{100 + i * 4}"

        # Generate departure time (between 6 AM and 9 PM)
        hour = (6 + (i * 2)) % 15 + 6  # 6 AM to 9 PM
        minute = (i * 13) % 60
        departure_time = f"{hour:02d}:{minute:02d}"

        # Generate flight duration based on route
        # Simplified calculation - in reality would depend on distance between cities
        duration_hours = 1 + (i % 3)  # 1-3 hours
        duration_minutes = (i * 10) % 60

        # Calculate arrival time
        arrival_hour = (hour + duration_hours) % 24
        arrival_minute = (minute + duration_minutes) % 60
        arrival_time = f"{arrival_hour:02d}:{arrival_minute:02d}"

        # Determine if flight has stops
        stops = 0 if i < (num_flights * 0.7) else 1  # 70% direct flights, 30% with 1 stop

        # Generate price based on airline, duration, and stops
        base_price = 2500 + (i * 500)  # Base price in INR
        if stops > 0:
            base_price *= 0.9  # Slight discount for flights with stops
        if duration_hours > 2:
            base_price *= 1.2  # Premium for longer flights
        if airline in ["Vistara", "Air India"]:
            base_price *= 1.15  # Premium for full-service airlines

        # Add some randomness to price
        price = int(base_price * (0.95 + random.random() * 0.2))  # +/- 10% variation

        # Generate seats available
        seats_available = 5 + (i * 2) % 20  # 5-24 seats available

        flight = {
            "airline": airline,
            "flight_number": flight_number,
            "origin": origin,
            "destination": destination,
            "departure_date": date_str,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration": f"{duration_hours}h {duration_minutes}m",
            "price": price,
            "seats_available": seats_available,
            "stops": stops
        }

        flight_data.append(flight)

    # Sort by price
    flight_data.sort(key=lambda x: x["price"])

    return flight_data


def get_destination_info(destination: str) -> Dict[str, Any]:
    """Get information about a destination (simulated)"""

    # Dictionary of popular Indian destinations and their highlights
    destinations = {
        "Kashmir": {
            "highlights": ["Dal Lake", "Gulmarg", "Pahalgam", "Sonamarg", "Mughal Gardens", "Shalimar Bagh"],
            "best_season": "April to October",
            "cuisine": ["Rogan Josh", "Yakhni", "Dum Aloo", "Kahwa"],
            "activities": ["Shikara Ride", "Skiing", "Trekking", "Cable Car Ride", "Shopping for Pashmina",
                           "Houseboat Stay"],
            "typical_duration": "5-7 days",
            "accommodation": ["Houseboat on Dal Lake", "Luxury Resorts in Gulmarg", "Hotels in Srinagar"]
        },
        "Goa": {
            "highlights": ["Baga Beach", "Calangute Beach", "Anjuna Beach", "Dudhsagar Falls", "Fort Aguada",
                           "Basilica of Bom Jesus"],
            "best_season": "November to February",
            "cuisine": ["Seafood", "Vindaloo", "Xacuti", "Feni"],
            "activities": ["Beach Activities", "Water Sports", "Nightlife", "Spice Plantation Tour", "Church Visits",
                           "Beach Shack Dining"],
            "typical_duration": "3-5 days",
            "accommodation": ["Beach Resorts", "Boutique Hotels", "Luxury Villas"]
        },
        "Kerala": {
            "highlights": ["Alleppey Backwaters", "Munnar", "Kovalam Beach", "Thekkady", "Wayanad", "Kochi"],
            "best_season": "September to March",
            "cuisine": ["Appam with Stew", "Kerala Fish Curry", "Puttu", "Avial"],
            "activities": ["Houseboat Stay", "Ayurvedic Treatments", "Wildlife Safari", "Tea Gardens Visit",
                           "Cultural Performances", "Backwater Cruise"],
            "typical_duration": "6-8 days",
            "accommodation": ["Houseboats", "Beach Resorts", "Plantation Stays", "Ayurvedic Retreats"]
        },
        "Rajasthan": {
            "highlights": ["Jaipur", "Udaipur", "Jodhpur", "Jaisalmer", "Pushkar", "Ranthambore"],
            "best_season": "October to March",
            "cuisine": ["Dal Baati Churma", "Laal Maas", "Ker Sangri", "Ghevar"],
            "activities": ["Palace Tours", "Desert Safari", "Elephant Ride", "City Tours", "Shopping for Handicrafts",
                           "Cultural Performances"],
            "typical_duration": "7-10 days",
            "accommodation": ["Heritage Hotels", "Palace Hotels", "Desert Camps", "Luxury Resorts"]
        },
        "Himachal Pradesh": {
            "highlights": ["Shimla", "Manali", "Dharamshala", "Dalhousie", "Kasol", "Spiti Valley"],
            "best_season": "March to June and September to November",
            "cuisine": ["Sidu", "Dham", "Chha Gosht", "Babru"],
            "activities": ["Trekking", "Paragliding", "River Rafting", "Camping", "Cultural Exploration",
                           "Hot Springs"],
            "typical_duration": "5-7 days",
            "accommodation": ["Mountain Resorts", "Cottages", "Homestays", "Luxury Hotels"]
        }
    }

    # Look for the destination or return a generic template
    for dest, info in destinations.items():
        if dest.lower() in destination.lower() or destination.lower() in dest.lower():
            return {
                "name": dest,
                **info
            }

    # Return generic info if specific destination not found
    return {
        "name": destination,
        "highlights": [f"Popular attractions in {destination}", f"Cultural experiences in {destination}",
                       f"Natural beauty of {destination}"],
        "best_season": "Varies by specific location",
        "cuisine": ["Local specialties", "Regional delicacies", "Traditional dishes"],
        "activities": ["Sightseeing", "Cultural Experiences", "Local Adventures", "Shopping", "Relaxation"],
        "typical_duration": f"{min(duration, 7)} days",
        "accommodation": ["Hotels", "Resorts", "Local Stays"]
    }


def generate_itinerary(destination: str, duration: int, destination_info: Dict[str, Any], interests: List[str]) -> List[
    Dict[str, Any]]:
    """Generate a detailed itinerary for the destination"""
    itinerary = []

    highlights = destination_info.get("highlights", [])
    activities = destination_info.get("activities", [])
    cuisine = destination_info.get("cuisine", [])
    accommodation_options = destination_info.get("accommodation", ["Hotel"])

    # Create a day-by-day itinerary
    for day in range(1, duration + 1):
        day_data = {
            "title": f"Exploring {destination}" if day > 1 else f"Arrival in {destination}"
        }

        if day == 1:
            # First day - arrival and light activities
            day_data.update({
                "morning": f"Arrival in {destination}. Check-in to your {random.choice(accommodation_options).lower()}.",
                "afternoon": f"Rest and refresh. Have lunch at a local restaurant sampling {random.choice(cuisine) if cuisine else 'local cuisine'}.",
                "evening": f"Brief orientation walk around your accommodation area. Dinner at a recommended local restaurant.",
                "accommodation": f"{random.choice(accommodation_options)} in {destination}",
                "notes": "Take it easy on your first day to acclimatize to the new surroundings."
            })
        elif day == duration:
            # Last day - departure
            day_data.update({
                "morning": f"Last-minute shopping for souvenirs and gifts.",
                "afternoon": "Check-out from accommodation. Enjoy a farewell lunch.",
                "evening": f"Departure from {destination} with wonderful memories.",
                "notes": "Keep some buffer time for unexpected delays before your departure."
            })
        else:
            # Regular days - sightseeing and activities
            # Pick highlights and activities not used yet
            remaining_highlights = [h for h in highlights if not any(h in d.values() for d in itinerary)]
            remaining_activities = [a for a in activities if not any(a in d.values() for d in itinerary)]

            # If we've used all, start reusing
            if not remaining_highlights:
                remaining_highlights = highlights
            if not remaining_activities:
                remaining_activities = activities

            # Prioritize interests if specified
            morning_activity = ""
            afternoon_activity = ""
            evening_activity = ""

            # Try to match interests with activities
            if interests:
                for interest in interests:
                    for activity in remaining_activities:
                        if interest.lower() in activity.lower():
                            if not morning_activity:
                                morning_activity = f"Visit {random.choice(remaining_highlights) if remaining_highlights else 'local attractions'} - {activity}"
                                continue
                            if not afternoon_activity:
                                afternoon_activity = f"Experience {activity} at {random.choice(remaining_highlights) if remaining_highlights else 'recommended locations'}"
                                continue

            # Fill in any missing activities
            if not morning_activity:
                morning_activity = f"Visit {random.choice(remaining_highlights) if remaining_highlights else 'local attractions'}"

            if not afternoon_activity:
                afternoon_activity = f"Explore {random.choice(remaining_highlights) if remaining_highlights else 'local sites'}. Try {random.choice(activities) if activities else 'local experiences'}"

            evening_activity = f"Enjoy {random.choice(cuisine) if cuisine else 'local cuisine'} for dinner. Experience the local nightlife or relax at your accommodation."

            day_data.update({
                "morning": morning_activity,
                "afternoon": afternoon_activity,
                "evening": evening_activity,
                "accommodation": f"{random.choice(accommodation_options)} in {destination}",
                "notes": "Adjust this day's schedule based on weather conditions and your energy level."
            })

        itinerary.append(day_data)

    return itinerary
