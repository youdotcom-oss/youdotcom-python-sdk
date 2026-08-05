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
import time
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
    ContentsFormats,
    WebSearchTool,
    ResearchEffort,
    FinanceResearchEffort,
    FinanceResearchResponse,
    ResearchResponse,
    TaskResponse,
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

    results = you.agents(request=ExpressAgentRunsRequest(
        input="What is the capital of France?",
        stream=False,
        tools=[
            WebSearchTool()
        ]
    ))

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

    response = you.agents(request=ExpressAgentRunsRequest(
        input="Restaurants in San Francisco",
        stream=True,
        tools=[
            WebSearchTool()
        ]
    ))

    # Type narrow to ensure we have a streaming response
    assert isinstance(response, eventstreaming.EventStream), "Expected streaming response"
    with response as stream:
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

    results = you.agents(request=request)

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
        results = you.agents(request=request)
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

    results = you.search(
        query="artificial intelligence in farming",
        count=1,
        livecrawl=LiveCrawl.WEB,
        livecrawl_formats=[LiveCrawlFormats.MARKDOWN]
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
    
    In 2.0.0, the Contents API now uses:
    - formats: Array of format types ('html', 'markdown', 'metadata')
    - crawl_timeout: Optional timeout between 1-60 seconds
    """
    print("\n🚀 Running Content Request...\n")

    assert you is not None, "SDK client not initialized"

    # Example 1: Get markdown content
    print("Example 1: Fetching markdown content...")
    results = you.contents(
        urls=["https://you.com"],
        formats=[ContentsFormats.MARKDOWN]
    )
    print(f"Received {len(results)} result(s)")
    for result in results:
        print(f"  URL: {result.url}")
        print(f"  Title: {result.title}")
        if result.markdown:
            print(f"  Markdown preview: {result.markdown[:100]}...")
    
    print("\n" + "-" * 40 + "\n")
    
    # Example 2: Get multiple formats including metadata (json+ld, opengraph info)
    print("Example 2: Fetching HTML + metadata...")
    results = you.contents(
        urls=["https://you.com"],
        formats=[ContentsFormats.HTML, ContentsFormats.METADATA],
        crawl_timeout=30  # Optional: set custom timeout (1-60 seconds)
    )
    print(f"Received {len(results)} result(s)")
    for result in results:
        print(f"  URL: {result.url}")
        print(f"  Title: {result.title}")
        if result.metadata:
            print(f"  Metadata - Site Name: {result.metadata.site_name}")
            print(f"  Metadata - Favicon: {result.metadata.favicon_url}")
    
    print()


def research_request():
    """
    Research API endpoint for comprehensive, multi-step research answers
    """
    print("\n🚀 Running Research Request...\n")

    assert you is not None, "SDK client not initialized"

    res = you.research(
        input="Which global cities improved air quality the most over the past 10 years, and what measurable actions contributed?",
        research_effort=ResearchEffort.STANDARD,
    )

    assert isinstance(res, ResearchResponse)
    print("Research Answer:")
    # `output.content` is a string when content_type is "text"
    print(res.output.content[:500] + "..." if len(res.output.content) > 500 else res.output.content)

    if res.output.sources:
        print(f"\nSources ({len(res.output.sources)}):")
        for source in res.output.sources:
            print(f"  - {source.title or 'Untitled'}: {source.url}")


def research_background_request():
    """
    Research API with background mode: returns a task handle instead of the final answer.
    Poll status with `you.get_research_task(task_id)` or stream events with
    `you.stream_research_task(task_id)`.
    """
    print("\n🚀 Running Research Background Request...\n")

    assert you is not None, "SDK client not initialized"

    res = you.research(
        input="Compare the profitability of NVIDIA, AMD, and Intel over the past 5 fiscal years.",
        research_effort=ResearchEffort.DEEP,
        background=True,
    )

    assert isinstance(res, TaskResponse)
    print(f"Queued task {res.task_id} (status: {res.status.value})")
    print(f"Stream URL: {res.stream_url}")

    # Optional: poll until completion
    print("\nPolling for completion...")
    while True:
        status_res = you.get_research_task(task_id=res.task_id)
        status = status_res.status.value
        print(f"  status: {status}")
        if status in ("completed", "failed", "cancelled"):
            break
        time.sleep(5)

    if status == "completed":
        # The Result model uses extra="allow", so model_dump() recovers
        # the full ResearchResponse payload from the task detail.
        print("\nFinal answer (preview):")
        payload = status_res.result.model_dump() if status_res.result else {}
        content = payload.get("output", {}).get("content", "")
        if isinstance(content, str):
            print(content[:500] + ("..." if len(content) > 500 else ""))


def research_and_wait_example():
    """
    Research API with the research_and_wait helper: submit in background
    mode and wait for completion in one call. Returns the final TaskDetail.
    """
    from youdotcom.research_helpers import research_and_wait
    from youdotcom.models import TaskDetail

    print("\n🚀 Running Research and Wait (Helper)...\n")

    assert you is not None, "SDK client not initialized"

    try:
        detail = research_and_wait(
            you,
            timeout_s=120.0,
            input="Compare the profitability of NVIDIA, AMD, and Intel over the past 5 fiscal years.",
            research_effort=ResearchEffort.DEEP,
        )
    except TypeError as e:
        if "TaskResponse" in str(e):
            print("  Background mode not enabled on server. Skipping.")
            return
        raise

    assert isinstance(detail, TaskDetail)
    print(f"Task completed: {detail.status.value}")
    if detail.result:
        payload = detail.result.model_dump()
        content = payload.get("output", {}).get("content", "")
        if isinstance(content, str):
            print(f"\nAnswer (preview):\n{content[:500]}...")


def research_stream_example():
    """
    Research API with streaming: submit in background mode, then stream
    real-time SSE events with the tolerant stream_research helper.

    The tolerant helper surfaces undocumented intermediate event types
    (e.g. research.searching, response.created) as raw dicts instead of
    crashing on pydantic validation. Recommended over the generated
    you.stream_research_task() for real tasks.
    """
    from youdotcom.research_helpers import research_background, stream_research

    print("\n🚀 Running Research Stream (Helper)...\n")

    assert you is not None, "SDK client not initialized"

    try:
        task = research_background(
            you,
            input="Compare the profitability of NVIDIA, AMD, and Intel over the past 5 fiscal years.",
            research_effort=ResearchEffort.DEEP,
        )
    except TypeError as e:
        if "TaskResponse" in str(e):
            print("  Background mode not enabled on server. Skipping.")
            return
        raise

    print(f"Queued task {task.task_id}, streaming events...\n")

    for event in stream_research(you, task_id=task.task_id):
        print(f"  event: {event.event}  data: {str(event.data)[:120]}")
        if event.event in ("response.done", "complete", "completed"):
            print("\n  Task completed via stream.")
            break
        if event.event in ("error", "failed", "cancelled"):
            print(f"\n  Task ended with: {event.event}")
            break

    # Fetch the final result via a GET
    detail = you.get_research_task(task_id=task.task_id)
    if detail.status.value == "completed" and detail.result:
        payload = detail.result.model_dump()
        content = payload.get("output", {}).get("content", "")
        if isinstance(content, str):
            print(f"\nFinal answer (preview):\n{content[:500]}...")


def research_output_schema_request():
    """
    Research API with `output_schema` for structured JSON output.
    """
    print("\n🚀 Running Research with output_schema...\n")

    assert you is not None, "SDK client not initialized"

    res = you.research(
        input="Are \"Acme Logistics LLC\" (Delaware) and \"Acme Logistics\" (Newark, NJ) the same business?",
        research_effort=ResearchEffort.STANDARD,
        output_schema={
            "type": "object",
            "properties": {
                "same_entity": {"type": "boolean"},
                "confidence": {"type": "number"},
                "evidence": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["same_entity", "confidence", "evidence"],
            "additionalProperties": False,
        },
    )

    assert isinstance(res, ResearchResponse)
    print(f"content_type: {res.output.content_type.value}")
    # output.content is Union[str, Dict[str, Any]] via the overlay's
    # additionalProperties: true. When content_type is "object" it is a
    # plain dict, so index it directly.
    structured_content = res.output.content
    print(f"structured payload: {structured_content}")


def finance_research_request():
    """
    Finance Research API endpoint for finance-focused multi-step research.
    Returns a Markdown answer with citations from financial sources (SEC filings,
    earnings releases, analyst coverage, market data) instead of the open web.
    """
    print("\n🚀 Running Finance Research Request...\n")

    assert you is not None, "SDK client not initialized"

    res = you.finance_research(
        input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?",
        research_effort=FinanceResearchEffort.DEEP,
    )

    assert isinstance(res, FinanceResearchResponse)
    print("Finance Answer:")
    # Finance Research always returns `content` as a Markdown string (content_type: "text").
    print(res.output.content[:500] + "..." if len(res.output.content) > 500 else res.output.content)

    if res.output.sources:
        print(f"\nSources ({len(res.output.sources)}):")
        for source in res.output.sources:
            print(f"  - {source.title or 'Untitled'}: {source.url}")


def search_request_with_boost():
    """
    Search API: use `boost_domains` to prefer certain domains in ranking
    without excluding other domains. Useful when you want sources-with-preference
    rather than a strict allow-list (`include_domains`).
    """
    print("\n🚀 Running Search Request (boost_domains)...\n")

    assert you is not None, "SDK client not initialized"

    results = you.search(
        query="latest advances in fusion energy research",
        count=5,
        boost_domains=["nature.com", "science.org", "arxiv.org"],
    )

    print("Top results:")
    if results.results and results.results.web:
        for result in results.results.web[:5]:
            print(f"  - {result.title or 'Untitled'}: {result.url}")


def content_request_with_max_age():
    """
    Contents API: use `max_age` to control cache freshness (in seconds).
    Pass `max_age=0` to always re-fetch, or e.g. `max_age=86400` to require
    cached content less than 24 hours old.
    """
    print("\n🚀 Running Content Request (max_age)...\n")

    assert you is not None, "SDK client not initialized"

    results = you.contents(
        urls=["https://example.com/page"],
        formats=[ContentsFormats.MARKDOWN],
        crawl_timeout=20,
        max_age=86400,  # require cache less than 24 hours old
    )

    for result in results:
        print(f"  URL: {result.url}")
        if result.markdown:
            print(f"  Markdown preview: {result.markdown[:120]}...")


# Available functions menu
FUNCTIONS = [
    {"name": "Express Batch Request", "fn": express_batch_request},
    {"name": "Express Streaming Request", "fn": express_streaming_request},
    {"name": "Advanced Batch Request", "fn": advanced_batch_request},
    {"name": "Custom Batch Request", "fn": custom_batch_request},
    {"name": "Search Request", "fn": search_request},
    {"name": "Search Request (boost_domains)", "fn": search_request_with_boost},
    {"name": "Content Request", "fn": content_request},
    {"name": "Content Request (max_age)", "fn": content_request_with_max_age},
    {"name": "Research Request", "fn": research_request},
    {"name": "Research Background Mode", "fn": research_background_request},
    {"name": "Research and Wait (Helper)", "fn": research_and_wait_example},
    {"name": "Research Stream (Helper)", "fn": research_stream_example},
    {"name": "Research with output_schema", "fn": research_output_schema_request},
    {"name": "Finance Research Request", "fn": finance_research_request},
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
