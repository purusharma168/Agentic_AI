import streamlit as st
import os
import pandas as pd
from datetime import datetime
from agent import process_query, get_flight_data

# Set page configuration
st.set_page_config(
    page_title="Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

# Define app styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 600;
        color: #1E88E5;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #424242;
    }
    .card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .info-text {
        font-size: 1rem;
        color: #616161;
    }
</style>
""", unsafe_allow_html=True)

# Create sidebar
with st.sidebar:
    st.markdown('<p class="sub-header">API Configuration</p>', unsafe_allow_html=True)

    # API key inputs
    nvidia_api_key = st.text_input("NVIDIA API Key",
                                   value=os.environ.get("NVIDIA_API_KEY",
                                                        "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"),
                                   type="password")
    serper_api_key = st.text_input("Serper API Key",
                                   value=os.environ.get("SERPER_API_KEY", "YOUR_SERPER_API_KEY"),
                                   type="password")

    if st.button("Save API Keys"):
        os.environ["NVIDIA_API_KEY"] = nvidia_api_key
        os.environ["SERPER_API_KEY"] = serper_api_key
        st.success("API keys saved!")

    st.markdown("---")

    # Example queries
    st.markdown('<p class="info-text">Sample Queries:</p>', unsafe_allow_html=True)

    with st.expander("Flight Search Examples"):
        st.markdown("""
        - "Find flights from Delhi to Mumbai for next week"
        - "I need to book a flight from Bangalore to Kolkata on May 10th" 
        - "Show me flights from Chennai to Goa this weekend"
        """)

    with st.expander("Itinerary Planning Examples"):
        st.markdown("""
        - "I am going to Kashmir for 5 days, plan my itinerary"
        - "Plan a 3-day trip to Goa" 
        - "What should I do in Kerala for a week-long vacation?"
        """)

# Main app content
st.markdown('<p class="main-header">Travel Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="info-text">Your AI-powered travel planning and flight booking assistant</p>',
            unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize flight data
if "flight_data" not in st.session_state:
    st.session_state.flight_data = None

# Initialize itinerary data
if "itinerary_data" not in st.session_state:
    st.session_state.itinerary_data = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about flights, destinations, or itineraries..."):
    # Display user message
    st.chat_message("user").markdown(prompt)

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            response, data_type, data = process_query(prompt)
            st.markdown(response)

            # Check if we have flight data to display
            if data_type == "flight" and data:
                st.session_state.flight_data = data
                st.session_state.itinerary_data = None

                # Convert to DataFrame for display
                try:
                    df = pd.DataFrame(data)

                    st.markdown("### Available Flights")

                    # Add filters
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if 'airline' in df.columns and len(df['airline'].unique()) > 0:
                            airlines = st.multiselect("Airlines", options=df["airline"].unique(),
                                                      default=df["airline"].unique())
                        else:
                            airlines = None

                    with col2:
                        if 'price' in df.columns:
                            min_price = float(df["price"].min()) if not df["price"].empty else 0
                            max_price = float(df["price"].max()) if not df["price"].empty else 50000
                            price_range = st.slider("Price Range (₹)",
                                                    min_value=min_price,
                                                    max_value=max_price,
                                                    value=(min_price, max_price))
                        else:
                            price_range = None

                    with col3:
                        if 'stops' in df.columns and len(df['stops'].unique()) > 0:
                            stops = st.multiselect("Stops", options=df["stops"].unique(), default=df["stops"].unique())
                        else:
                            stops = None

                    # Apply filters if they exist
                    filtered_df = df.copy()
                    if airlines:
                        filtered_df = filtered_df[filtered_df["airline"].isin(airlines)]
                    if price_range:
                        filtered_df = filtered_df[
                            (filtered_df["price"] >= price_range[0]) & (filtered_df["price"] <= price_range[1])]
                    if stops is not None:
                        filtered_df = filtered_df[filtered_df["stops"].isin(stops)]

                    # Display filtered results
                    if not filtered_df.empty:
                        display_cols = [col for col in ["airline", "flight_number", "origin", "destination",
                                                        "departure_date", "departure_time", "arrival_time",
                                                        "duration", "price", "seats_available", "stops"]
                                        if col in filtered_df.columns]

                        st.dataframe(filtered_df[display_cols], use_container_width=True)

                        # Flight selection
                        selected_flight = st.selectbox("Select a flight to book",
                                                       options=filtered_df.index,
                                                       format_func=lambda
                                                           i: f"{filtered_df.loc[i, 'airline']} - {filtered_df.loc[i, 'origin']} to {filtered_df.loc[i, 'destination']} - ₹{filtered_df.loc[i, 'price']}" if all(
                                                           col in filtered_df.columns for col in
                                                           ['airline', 'origin', 'destination',
                                                            'price']) else f"Flight {i}")

                        passenger_info_expander = st.expander("Enter Passenger Information")
                        with passenger_info_expander:
                            col1, col2 = st.columns(2)
                            with col1:
                                name = st.text_input("Full Name")
                                email = st.text_input("Email")
                                phone = st.text_input("Phone Number")
                            with col2:
                                age = st.number_input("Age", min_value=1, max_value=120, value=30)
                                gender = st.selectbox("Gender", options=["Male", "Female", "Other"])
                                id_type = st.selectbox("ID Type", options=["Aadhaar", "PAN Card", "Passport"])
                                id_number = st.text_input("ID Number")

                        if st.button("Book Flight"):
                            if name and email and phone:
                                st.success(f"Booking confirmed for {name}!")
                                st.info("Booking details have been sent to your email and phone.")

                                # Display booking summary
                                booking_summary = {
                                    "Passenger": name,
                                    "Flight": f"{filtered_df.loc[selected_flight, 'airline']} {filtered_df.loc[selected_flight, 'flight_number']}" if all(
                                        col in filtered_df.columns for col in
                                        ['airline', 'flight_number']) else "Selected Flight",
                                    "Route": f"{filtered_df.loc[selected_flight, 'origin']} to {filtered_df.loc[selected_flight, 'destination']}" if all(
                                        col in filtered_df.columns for col in
                                        ['origin', 'destination']) else "Selected Route",
                                    "Date": filtered_df.loc[
                                        selected_flight, 'departure_date'] if 'departure_date' in filtered_df.columns else "Scheduled Date",
                                    "Time": f"{filtered_df.loc[selected_flight, 'departure_time']}" if 'departure_time' in filtered_df.columns else "Scheduled Time",
                                    "Amount Paid": f"₹{filtered_df.loc[selected_flight, 'price']}" if 'price' in filtered_df.columns else "₹0"
                                }

                                st.json(booking_summary)
                            else:
                                st.error("Please fill in all required passenger information.")
                    else:
                        st.warning("No flights match your filter criteria. Please adjust your filters.")
                except Exception as e:
                    st.error(f"Error displaying flight data: {str(e)}")

            # Check if we have itinerary data to display
            elif data_type == "itinerary" and data:
                st.session_state.itinerary_data = data
                st.session_state.flight_data = None

                st.markdown("### Your Travel Itinerary")

                # Display the itinerary in a more structured way
                for day_num, day_data in enumerate(data, 1):
                    with st.expander(f"Day {day_num}: {day_data.get('title', 'Activities')}"):
                        st.markdown(f"**Morning:** {day_data.get('morning', 'No activities planned')}")
                        st.markdown(f"**Afternoon:** {day_data.get('afternoon', 'No activities planned')}")
                        st.markdown(f"**Evening:** {day_data.get('evening', 'No activities planned')}")

                        if 'accommodation' in day_data:
                            st.markdown(f"**Accommodation:** {day_data['accommodation']}")

                        if 'notes' in day_data:
                            st.markdown(f"**Notes:** {day_data['notes']}")

                # Add a download button for the itinerary
                if st.button("Download Itinerary (PDF)"):
                    st.info("This would generate a PDF of your itinerary in a real application.")

                # Add a share button
                if st.button("Share Itinerary"):
                    st.info("This would allow you to share the itinerary via email or message in a real application.")

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})
