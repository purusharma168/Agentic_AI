from openai import OpenAI


def get_llm_response(query):
    # Setup the client with NVIDIA's API
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=""  # Replace with your actual API key
    )

    # Create the messages for the API call
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": query}
    ]

    # Generate the response
    response = client.chat.completions.create(
        model="nvidia/llama-3.3-nemotron-super-49b-v1",
        messages=messages,
        temperature=0.6,
        top_p=0.95,
        max_tokens=4096
    )

    return response.choices[0].message.content


# Direct CLI interaction when this file is run directly
if __name__ == "__main__":
    user_query = input("What would you like to ask? ")
    print("Generating response...\n")

    response_text = get_llm_response(user_query)

    print("Response:")
    print(response_text)
    print("\nResponse complete!")
