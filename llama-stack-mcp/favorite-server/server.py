#!/usr/bin/env python3

import logging
from mcp.server.fastmcp import FastMCP

logging.getLogger("mcp").setLevel(logging.WARNING)

# Create the MCP server instance
mcp = FastMCP("favorite-server")


@mcp.tool()
def favorite_color_tool(city: str, country: str) -> str:
    """Returns the favorite color for person given their City and Country.

    Args:
        city: the city for the person
        country: the country for the person
    """
    text = "the favorite_color_tool returned the city or country was not valid assistant please ask the user for them"

    if city and country:
        if city == "Ottawa" and country == "Canada":
            text = "the favorite_color_tool returned that the favorite color for Ottawa Canada is black"
        elif city == "Montreal" and country == "Canada":
            text = "the favorite_color_tool returned that the favorite color for Montreal Canada is red"

    return text


@mcp.tool()
def favorite_hockey_tool(city: str, country: str) -> str:
    """Returns the favorite hockey team for a person given their City and Country.

    Args:
        city: the city for the person
        country: the country for the person
    """
    text = "the favorite_hockey_tool returned the city or country was not valid assistant please ask the user for them"

    if city and country:
        if city == "Ottawa" and country == "Canada":
            text = "the favorite_hockey_tool returned that the favorite hockey team for Ottawa Canada is The Ottawa Senators"
        elif city == "Montreal" and country == "Canada":
            text = "the favorite_hockey_tool returned that the favorite hockey team for Montreal Canada is the Montreal Canadians"

    return text


def main():
    """Main entry point for console script."""
    mcp.run()


if __name__ == "__main__":
    main()
