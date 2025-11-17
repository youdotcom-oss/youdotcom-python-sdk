import sys

from youdotcom import You
from youdotcom.models import Format
from youdotcom.types.typesafe_models import (
    print_contents,
    Format,
)

def fetch_html_content(you: You):
    """Fetch HTML content from URLs."""
    res = you.contents.generate(
        urls=[
            "https://www.python.org",
            "https://www.example.com",
        ],
        format_=Format.HTML,
    )
    print_contents(res)


def fetch_markdown_content(you: You):
    """Fetch Markdown content from URLs."""
    res = you.contents.generate(
        urls=[
            "https://www.python.org",
        ],
        format_=Format.MARKDOWN,
    )
    print_contents(res)


def fetch_multiple_urls(you: You):
    """Fetch content from multiple URLs."""
    res = you.contents.generate(
        urls=[
            "https://www.you.com",
            "https://www.github.com",
            "https://www.python.org",
        ],
        format_=Format.MARKDOWN,
    )
    print_contents(res)


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python contents.py <api_key>", file=sys.stderr)
        sys.exit(1)

    api_key = sys.argv[1]

    with You(api_key_auth=api_key) as you:
        # Fetch HTML content
        fetch_html_content(you)
        
        # Fetch Markdown content
        # fetch_markdown_content(you)
        
        # Fetch multiple URLs
        # fetch_multiple_urls(you)


if __name__ == "__main__":
    main()

