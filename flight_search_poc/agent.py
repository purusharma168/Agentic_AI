import os
import json
import re
from typing import List, Dict, Any, TypedDict, Tuple, Union
from datetime import datetime, timedelta
from openai import OpenAI
from langgraph.graph import StateGraph, END

from tools import web_search_flights, extract_flight_info, plan_itinerary


# Define our state for the agent
class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    tools: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_outputs: List[Dict[str, Any]]
    current_query: str
    next: str


# Setup the OpenAI client for NVIDIA's API
def get_nvidia_client(api_key=None):
    if api_key is None:
        api_key = os.environ.get("NVIDIA_API_KEY",
                                 "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")

    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )


# Create a simple tool executor
class SimpleToolExecutor:
    def __init__(self, tools):
        self.tools = tools

    def execute(self, tool_request):
        name = tool_request["name"]
        args = tool_request["arguments"]

        if name not in self.tools:
            return f"Error: Tool '{name}' not found"

        tool_fn = self.tools[name]

        try:
            if args:
                return tool_fn(**args)
            else:
                return tool_fn()
        except Exception as e:
            return f"Error executing {name}: {str(e)}"


# Define tools in the format expected by the model
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search_flights",
            "description": "Search the web for current flight information based on user query, especially for Indian locations",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query for flight information, including origins, destinations, and dates"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_flight_info",
            "description": "Get specific flight details for a given date, origin, and destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "The date to search flights for, in format like '4 May 2025' or 'May 4, 2025'"
                    },
                    "origin": {
                        "type": "string",
                        "description": "The departure city or airport code (e.g., 'Delhi' or 'DEL')"
                    },
                    "destination": {
                        "type": "string",
                        "description": "The arrival city or airport code (e.g., 'Mumbai' or 'BOM')"
                    }
                },
                "required": ["date_str", "origin", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "plan_itinerary",
            "description": "Create a detailed travel itinerary for a destination",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {
                        "type": "string",
                        "description": "The destination for which to create an itinerary (e.g., 'Kashmir', 'Goa')"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "The number of days for the trip"
                    },
                    "interests": {
                        "type": "string",
                        "description": "Optional comma-separated list of traveler's interests (e.g., 'adventure, food, culture')"
                    }
                },
                "required": ["destination", "duration"]
            }
        }
    }
]

# Create our tool executor
TOOL_EXECUTOR = SimpleToolExecutor({
    "web_search_flights": web_search_flights,
    "extract_flight_info": extract_flight_info,
    "plan_itinerary": plan_itinerary
})


# Define routing logic
def router(state: AgentState) -> str:
    return state["next"]


# Define the agent nodes
def call_model(state: AgentState) -> AgentState:
    """Call the NVIDIA model to get a response"""
    client = get_nvidia_client()

    response = client.chat.completions.create(
        model="nvidia/llama-3.3-nemotron-super-49b-v1",
        messages=state["messages"],
        tools=state["tools"],
        temperature=0.6,
        top_p=0.95,
        max_tokens=4096
    )

    message = response.choices[0].message

    # Add the assistant's message to the history
    assistant_message = {"role": "assistant", "content": message.content}
    state["messages"].append(assistant_message)

    # Check if the model wants to use tools
    if hasattr(message, "tool_calls") and message.tool_calls:
        state["tool_calls"] = message.tool_calls
        state["next"] = "execute_tools"
    else:
        # No tools needed, we're done
        state["next"] = END

    return state


def execute_tools(state: AgentState) -> AgentState:
    """Execute tools based on the model's tool calls"""
    results = []

    for tool_call in state["tool_calls"]:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        # Execute the appropriate tool
        tool_result = TOOL_EXECUTOR.execute({
            "name": function_name,
            "arguments": function_args
        })

        # Format the result for the model
        results.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": str(tool_result)
        })

    # Add tool results to message history and state
    state["messages"].extend(results)
    state["tool_outputs"] = results

    # Let the model generate a new response that incorporates the tool outputs
    state["next"] = "call_model"

    return state


# LangGraph workflow setup
def build_agent():
    # Create the workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("call_model", call_model)
    workflow.add_node("execute_tools", execute_tools)

    # Add conditional edges
    workflow.add_conditional_edges(
        "call_model",
        router,
        {
            "execute_tools": "execute_tools",
            END: END
        }
    )

    workflow.add_conditional_edges(
        "execute_tools",
        router,
        {
            "call_model": "call_model"
        }
    )

    # Set the entry point
    workflow.set_entry_point("call_model")

    return workflow.compile()


# Process a single query through the agent
def process_query(query: str) -> Tuple[str, str, Union[List[Dict[str, Any]], None]]:
    """
    Process a user query through the agent and return the response,
    along with any flight or itinerary data

    Returns:
        Tuple containing (response_text, data_type, data)
        - response_text: The textual response from the agent
        - data_type: Either "flight", "itinerary", or None
        - data: The structured data for flights or itinerary, or None
    """
    system_message = """You are a helpful travel assistant for Indian travelers with access to real-time information.
When a user asks about booking a flight, ALWAYS use the web_search_flights tool first to find general information,
then use the extract_flight_info tool to get specific flight details.

If the user doesn't provide complete information for flight search:
1. Ask for the origin city if not provided
2. Ask for the destination city if not provided
3. Ask for the travel date if not provided

IMPORTANT: If the user asks for flights on a past date, inform them politely that booking past flights is not possible.

If the user asks about travel itineraries or planning a trip to a specific destination, use the plan_itinerary tool
to create a detailed day-by-day plan.

For Indian travelers, focus on providing information relevant to Indian locations, airlines, and travel considerations.

Be conversational, helpful, and provide comprehensive information."""

    # Initialize the state
    state = {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ],
        "tools": TOOLS,
        "tool_calls": [],
        "tool_outputs": [],
        "current_query": query,
        "next": "call_model"  # Initial state
    }

    # Create our agent
    agent = build_agent()

    # Execute the agent graph
    result = agent.invoke(state)

    # Find all assistant messages
    assistant_messages = [msg for msg in result["messages"] if msg["role"] == "assistant"]

    # Find all tool outputs
    tool_outputs = [msg for msg in result["messages"] if msg["role"] == "tool"]

    # Extract structured data if available
    flight_data = None
    itinerary_data = None
    data_type = None

    for output in tool_outputs:
        if output["name"] == "extract_flight_info":
            try:
                # Try to extract flight data from the output
                flight_data = extract_flight_data_from_output(output["content"])
                data_type = "flight"
            except:
                pass

        elif output["name"] == "plan_itinerary":
            try:
                # Try to extract itinerary data from the output
                itinerary_data = extract_itinerary_data_from_output(output["content"])
                data_type = "itinerary"
            except:
                pass

    # Return the final assistant message and any structured data
    if assistant_messages:
        if data_type == "flight":
            return assistant_messages[-1]["content"], data_type, flight_data
        elif data_type == "itinerary":
            return assistant_messages[-1]["content"], data_type, itinerary_data
        else:
            return assistant_messages[-1]["content"], None, None
    else:
        return "No response generated", None, None


def extract_flight_data_from_output(output: str) -> List[Dict[str, Any]]:
    """
    Extract structured flight data from the tool output text
    """
    flight_data = []

    # Check if we have any flight information in the output
    if "Flight information" not in output:
        return flight_data

    # Split by flight entries
    flight_entries = re.split(r"Flight \d+:", output)

    for entry in flight_entries[1:]:  # Skip the first split which is header text
        flight = {}

        # Extract airline and flight number
        airline_match = re.search(r"([A-Za-z\s]+) ([A-Z][0-9]+)", entry)
        if airline_match:
            flight["airline"] = airline_match.group(1).strip()
            flight["flight_number"] = airline_match.group(2).strip()

        # Extract route
        route_match = re.search(r"Route: ([A-Z]+) to ([A-Z]+)", entry)
        if route_match:
            flight["origin"] = route_match.group(1).strip()
            flight["destination"] = route_match.group(2).strip()

        # Extract date
        date_match = re.search(r"Date: ([0-9]{4}-[0-9]{2}-[0-9]{2})", entry)
        if date_match:
            flight["departure_date"] = date_match.group(1).strip()

        # Extract departure time
        departure_match = re.search(r"Departure: ([0-9]{2}:[0-9]{2})", entry)
        if departure_match:
            flight["departure_time"] = departure_match.group(1).strip()

        # Extract arrival time
        arrival_match = re.search(r"Arrival: ([0-9]{2}:[0-9]{2})", entry)
        if arrival_match:
            flight["arrival_time"] = arrival_match.group(1).strip()

        # Extract duration
        duration_match = re.search(r"Duration: ([0-9]+h [0-9]+m)", entry)
        if duration_match:
            flight["duration"] = duration_match.group(1).strip()

        # Extract stops
        stops_match = re.search(r"Stops: ([0-9]+)", entry)
        if stops_match:
            flight["stops"] = int(stops_match.group(1).strip())

        # Extract price
        price_match = re.search(r"Price: \$([0-9.]+)", entry)
        if price_match:
            # Convert USD to INR for Indian context
            flight["price"] = float(price_match.group(1).strip()) * 83  # Approximate INR conversion

        # Extract seats
        seats_match = re.search(r"Seats available: ([0-9]+)", entry)
        if seats_match:
            flight["seats_available"] = int(seats_match.group(1).strip())

        flight_data.append(flight)

    return flight_data


def extract_itinerary_data_from_output(output: str) -> List[Dict[str, Any]]:
    """
    Extract structured itinerary data from the tool output text
    """
    itinerary_data = []

    # Split by day
    days = re.split(r"Day \d+:", output)

    for i, day in enumerate(days[1:], 1):  # Skip the first split which is header text
        day_data = {
            "title": f"Day {i}"
        }

        # Try to extract a title for the day
        title_match = re.search(r"^([^\n]+)", day.strip())
        if title_match:
            day_data["title"] = title_match.group(1).strip()

        # Extract morning activities
        morning_match = re.search(r"Morning:([^\n]+)", day)
        if morning_match:
            day_data["morning"] = morning_match.group(1).strip()

        # Extract afternoon activities
        afternoon_match = re.search(r"Afternoon:([^\n]+)", day)
        if afternoon_match:
            day_data["afternoon"] = afternoon_match.group(1).strip()

        # Extract evening activities
        evening_match = re.search(r"Evening:([^\n]+)", day)
        if evening_match:
            day_data["evening"] = evening_match.group(1).strip()

        # Extract accommodation
        accommodation_match = re.search(r"Accommodation:([^\n]+)", day)
        if accommodation_match:
            day_data["accommodation"] = accommodation_match.group(1).strip()

        # Extract any notes
        notes_match = re.search(r"Notes:([^\n]+)", day)
        if notes_match:
            day_data["notes"] = notes_match.group(1).strip()

        itinerary_data.append(day_data)

    return itinerary_data


def get_flight_data(date_str: str, origin: str, destination: str) -> List[Dict[str, Any]]:
    """
    Utility function to get flight data directly (for use in the app)
    """
    result, _, flight_data = extract_flight_info(date_str, origin, destination)
    return flight_data
