import sys

from youdotcom import You
from youdotcom.types.typesafe_models import (
    print_search,
    Country,
    Freshness,
    LiveCrawl,
    LiveCrawlFormats,
    SafeSearch,
)

def basic_search(you: You):
    """Perform a basic unified search."""
    res = you.search.unified(
        query="latest AI developments",
    )
    print_search(res)


def search_with_filters(you: You):
    """Perform a search with filters applied."""
    
    res = you.search.unified(
        query="renewable energy",
        count=10,
        freshness=Freshness.WEEK,
        country=Country.US,
        safesearch=SafeSearch.MODERATE,
    )
    print_search(res)


def search_with_pagination(you: You):
    """Perform a search with pagination."""
    res = you.search.unified(
        query="python programming",
        count=5,
        offset=1,
    )
    print_search(res)


def search_with_livecrawl(you: You):
    """Perform a search with livecrawl enabled."""
    
    res = you.search.unified(
        query="machine learning tutorials",
        count=3,
        livecrawl=LiveCrawl.WEB,
        livecrawl_formats=LiveCrawlFormats.MARKDOWN,
    )
    print_search(res)


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python search.py <api_key>", file=sys.stderr)
        sys.exit(1)

    api_key = sys.argv[1]

    with You(api_key_auth=api_key) as you:
        # Basic search
        basic_search(you)
        
        # Search with filters
        # search_with_filters(you)
        
        # Search with pagination
        # search_with_pagination(you)
        
        # Search with livecrawl
        # search_with_livecrawl(you)


if __name__ == "__main__":
    main()

