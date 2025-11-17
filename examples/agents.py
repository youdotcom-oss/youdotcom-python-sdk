import sys

from youdotcom import You
from youdotcom.models import ComputeTool, WebSearchTool, ResearchTool
from youdotcom.types.typesafe_models import (
    AgentType,
    ChatAnswerFull,
    SearchEffort,
    Verbosity,
    WebSearchResultsFull,
    get_text_tokens,
    stream_text_tokens,
)


def express_agent(you: You):
    """Get the complete response without streaming."""
    res = you.agents.runs.create(
        agent=AgentType.EXPRESS,
        input="Teach me how to make an omelet",
        stream=False,
    )
    get_text_tokens(res)


def express_agent_streaming(you: You):
    """Stream the response using Server-Sent Events (SSE)."""
    res = you.agents.runs.create(
            agent=AgentType.EXPRESS,
            input="Teach me how to make an omelet",
            stream=True,
    )
    stream_text_tokens(res)


def express_agent_with_web_search_tool(you: You):
    """Get the complete response with web search tool enabled."""
    res = you.agents.runs.create(
            agent=AgentType.EXPRESS,
            input="Summarize today's top AI research headlines and cite sources.",
            stream=False,
            tools=[WebSearchTool()]
    ) 
    get_text_tokens(res)


def advanced_agent_with_research_tool(you: You):
    """Get the complete response with an advanced agent and the research tool enabled."""
    res = you.agents.runs.create(
            agent=AgentType.ADVANCED,
            input="Summarize today's top AI research headlines and cite sources.",
            stream=False,
            tools=[ResearchTool()]
    ) 
    get_text_tokens(res)


def advanced_agent_with_research_and_compute_tool(you: You):
    """Get the complete response with an advanced agent and the research and compute tools enabled."""
    res = you.agents.runs.create(
            agent=AgentType.ADVANCED,
            input="Research and calculate the latest trends and the square root of 169. Show your work.",
            stream=True,
            tools=[
                ComputeTool(),
                ResearchTool(
                    search_effort=SearchEffort.AUTO,
                    report_verbosity=Verbosity.HIGH,
                ),
            ]
    ) 
    stream_text_tokens(res)


def custom_agent(you: You):
    """Get the complete response using a custom agent."""
    res = you.agents.runs.create(
            agent="c12fa027-424e-4002-9659-746c16e74faa",
            input="Teach me how to make an omelet",
            stream=False,
    )
    get_text_tokens(res)


def stream_response_typesafe(you: You):
    """Stream the response using typesafe SSE event types.
    
    Demonstrates how to use the typesafe models to handle different SSE event types
    with proper type checking and pattern matching.
    """
    res = you.agents.runs.create(
            agent=AgentType.ADVANCED,
            input="Research and calculate the latest trends and the square root of 169. Show your work.",
            stream=True,
            tools=[
                ComputeTool(),
                ResearchTool(
                    search_effort=SearchEffort.AUTO,
                    report_verbosity=Verbosity.HIGH,
                ), 
            ]
    )

    with res as event_stream:
        for data in event_stream:
            if not data.response:
                continue
            
            response = data.response
            
            # Handle delta text
            if response.delta:
                print(response.delta, end="", flush=True)
            
            # Handle full response with type-safe pattern matching
            if response.full:
                full = response.full
                
                # Type-safe pattern matching on full response types
                if isinstance(full, ChatAnswerFull):
                    print(f"\n\nChat Answer: {full.text}")
                    if full.sources:
                        print("\nSources:")
                        for source in full.sources:
                            print(f"  - {source.title}: {source.url}")
                
                elif isinstance(full, WebSearchResultsFull):
                    if full.results:
                        print(f"\n\nWeb Search Results ({len(full.results)} results):")
                        for result in full.results:
                            print(f"  - {result.title}")
                            print(f"    URL: {result.url}")
                            if result.description:
                                print(f"    Description: {result.description}")


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python search_app.py <api_key>", file=sys.stderr)
        sys.exit(1)

    api_key = sys.argv[1]

    with You(api_key_auth=api_key) as you:

        # Express Agent
        express_agent(you) # Get complete response from express agent
        # express_agent_streaming(you) # Stream the response
        # express_agent_with_web_search_tool(you) # Get complete response with web search

        # Advanced Agent
        # advanced_agent_with_research_tool(you)
        # advanced_agent_with_research_and_compute_tool(you)

        # Custom Agent
        # custom_agent(you)
        
        # Typesafe SSE event handling
        # stream_response_typesafe(you)

if __name__ == "__main__":
    main()
