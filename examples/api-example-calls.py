#!/usr/bin/env python3
"""
API Example Calls for You.com Python SDK
Run this file to see interactive examples of all available API endpoints.

Setup Instructions:
-------------------
1. Create and activate a virtual environment:
   python3 -m venv venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

2. Install the package:
   pip install youdotcom

3. Run the script:
   python api-example-calls.py

   The script will prompt you to enter your API key at runtime.
"""

from typing import Optional
from youdotcom import You
from youdotcom.models import (
    ResearchTool,
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    SearchEffort,
    ReportVerbosity,
    CustomAgentRunsRequest,
    LiveCrawl,
    LiveCrawlFormats,
    ResponseCreated,
    ResponseStarting,
    ResponseOutputItemAdded,
    ResponseOutputContentFull,
    ResponseOutputItemDone,
    ResponseOutputTextDelta,
    ResponseDone,
    AgentRunsBatchResponse,
    AgentRunsStreamingResponse,
    ContentsFormat,
    WebSearchTool
)
from youdotcom.utils import eventstreaming

# Will be initialized with API key in main()
you: Optional[You] = None

def express_batch_request():
    """
    Express agent with batch (non-streaming) response
    """
    print("\n🚀 Running Express Batch Request...\n")

    assert you is not None, "SDK client not initialized"

    request = ExpressAgentRunsRequest(
        input="What is the capital of France?",
        stream=False,
        tools=[
            WebSearchTool()
        ]
    )

    results = you.agents.runs.create(request=request)

    res = you.agents.runs.create(request={
        "agent": "express",
        "input": "What is the capital of France?",
        "stream": False,
    })
    # Access the results - check if it's a batch response
    if isinstance(results, AgentRunsBatchResponse):
        if results.output:
            for output in results.output:
                if output.text:
                    print(output.text)
                    break
            else:
                print("No text response found in agent output")
        else:
            print("No response from agent")
    else:
        print("Unexpected response type")

def express_streaming_request():
    """
    Express agent with streaming response
    """
    print("\n🚀 Running Express Streaming Request...\n")

    assert you is not None, "SDK client not initialized"

    request = ExpressAgentRunsRequest(
        input="Restaurants in San Francisco",
        stream=True,
        tools=[
            WebSearchTool()
        ]
    )

    response = you.agents.runs.create(request=request)

    # Type narrow to ensure we have a streaming response
    assert isinstance(response, eventstreaming.EventStream), "Expected streaming response"
    stream: eventstreaming.EventStream[AgentRunsStreamingResponse] = response

    # Iterate through the stream and handle each event type
    # Each chunk is an AgentRunsStreamingResponse with a 'data' field
    for chunk in stream:
        # The data field contains the actual event (discriminated by TYPE)
        event_data = chunk.data

        # Use isinstance() to narrow the type and handle each event
        # This is the proper way to do a "switch statement" on Union types in Python
        if isinstance(event_data, ResponseCreated):
            print(f"✨ Response created (seq: {event_data.seq_id})")

        elif isinstance(event_data, ResponseStarting):
            print(f"🚀 Response starting (seq: {event_data.seq_id})")

        elif isinstance(event_data, ResponseOutputItemAdded):
            print(f"➕ Output item added: {event_data.seq_id}")

        elif isinstance(event_data, ResponseOutputContentFull):
            print("\n🔍 Web Search Results:")
            if event_data.response.full:
                for idx, result in enumerate(event_data.response.full, 1):
                    print(f"  {idx}. {result.title} - {result.url}")

        elif isinstance(event_data, ResponseOutputTextDelta):
            # Print the delta text as it streams in (without newline)
            print(event_data.response.delta, end='', flush=True)

        elif isinstance(event_data, ResponseOutputItemDone):
            print(f"\n✅ Output item done (index: {event_data.response.output_index})")

        elif isinstance(event_data, ResponseDone):
            print("\n🎉 Response completed!")
            print(f"   Runtime: {event_data.response.run_time_ms} seconds")
            print(f"   Finished: {event_data.response.finished}")

        else:
            print(f"⚠️  Unknown event type: {type(event_data).__name__}")


def advanced_batch_request():
    """
    Advanced agent with batch response
    """
    print("\n🚀 Running Advanced Batch Request...\n")

    assert you is not None, "SDK client not initialized"

    request = AdvancedAgentRunsRequest(
        input="What is the capital of France?",
        stream=False,
        tools=[
            ResearchTool(
                search_effort=SearchEffort.LOW,
                report_verbosity=ReportVerbosity.MEDIUM
            )
        ]
    )

    results = you.agents.runs.create(request=request)

    # Access the results - check if it's a batch response
    if isinstance(results, AgentRunsBatchResponse):
        if results.output:
            for output in results.output:
                if output.text:
                    print(output.text)
                    break
            else:
                print("No text response found in agent output")
        else:
            print("No response from agent")
    else:
        print("Unexpected response type")


def custom_batch_request():
    """
    Custom agent with batch response
    Note: Replace the agent ID with your own custom agent ID
    """
    print("\n🚀 Running Custom Batch Request...\n")

    assert you is not None, "SDK client not initialized"

    # Replace this with your actual custom agent ID
    custom_agent_id = "63773261-b4de-4d8f-9dfd-cff206a5cb51"

    request = CustomAgentRunsRequest(
        agent=custom_agent_id,
        input="What is the capital of France?",
        stream=False
    )

    try:
        results = you.agents.runs.create(request=request)
        print(results)
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure to use a valid custom agent ID")


def search_request():
    """
    Search API endpoint with livecrawl
    """
    print("\n🚀 Running Search Request...\n")

    assert you is not None, "SDK client not initialized"

    results = you.search.unified(
        query="artificial intelligence in farming",
        count=1,
        livecrawl=LiveCrawl.WEB,
        livecrawl_formats=LiveCrawlFormats.MARKDOWN
    )

    print("Metadata:")
    print(results.metadata)

    print("\nWeb Results:")
    if results.results and results.results.web:
        web_urls = [result.url for result in results.results.web]
        print(web_urls)
    else:
        print("No web results found")


def content_request():
    """
    Contents API endpoint to fetch page content
    """
    print("\n🚀 Running Content Request...\n")

    assert you is not None, "SDK client not initialized"

    results = you.contents.generate(
        urls=["https://you.com"],
        format_=ContentsFormat.MARKDOWN
    )

    print(results)


# Available functions menu
FUNCTIONS = [
    {"name": "Express Batch Request", "fn": express_batch_request},
    {"name": "Express Streaming Request", "fn": express_streaming_request},
    {"name": "Advanced Batch Request", "fn": advanced_batch_request},
    {"name": "Custom Batch Request", "fn": custom_batch_request},
    {"name": "Search Request", "fn": search_request},
    {"name": "Content Request", "fn": content_request},
]


def main():
    """
    Main interactive CLI menu
    """
    global you

    print("\n╔════════════════════════════════════════╗")
    print("║       You.com API Examples Menu        ║")
    print("╚════════════════════════════════════════╝\n")

    # Get API key from user
    api_key = input("🔑 Enter your You.com API key: ").strip()

    if not api_key:
        print("❌ API key is required to use the You.com API.")
        return

    # Initialize the SDK
    try:
        you = You(api_key_auth=api_key)
        print("\n✅ API key set!\n")
    except Exception as e:
        print(f"❌ Error initializing SDK: {e}")
        return

    # Show menu options
    for index, item in enumerate(FUNCTIONS, start=1):
        print(f"  [{index}] {item['name']}")
    print("  [0] Exit\n")

    # Get user choice
    try:
        choice = int(input("Select an option: "))
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
        return

    if choice == 0:
        print("Goodbye!")
        return

    if 1 <= choice <= len(FUNCTIONS):
        selected = FUNCTIONS[choice - 1]
        print(f"\nRunning: {selected['name']}...\n")
        try:
            selected['fn']()
        except Exception as e:
            print(f"\n❌ Error running {selected['name']}: {e}")
    else:
        print("❌ Invalid selection. Please try again.")


if __name__ == "__main__":
    main()
