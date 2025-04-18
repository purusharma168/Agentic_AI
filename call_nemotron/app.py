import streamlit as st
from cli import get_llm_response

# Page setup
st.set_page_config(page_title="LLM Chat", page_icon="🤖")
st.title("NVIDIA Llama 3.3 Nemotron Chat")

# Create the chat interface
st.write("Ask a question below:")

# User input form
with st.form(key="query_form"):
    user_query = st.text_input("Your question:", key="query")
    submit_button = st.form_submit_button("Ask")

# Process the query when submitted
if submit_button and user_query:
    # Show the user's query
    st.write(f"**Your question:** {user_query}")

    # Create a placeholder for the response
    response_container = st.container()

    with response_container:
        with st.spinner("Generating response..."):
            try:
                # Call the function from cli.py
                response_text = get_llm_response(user_query)

                # Display the response
                st.write("**Response:**")
                st.write(response_text)

            except Exception as e:
                st.error(f"Error generating response: {str(e)}")
