
from dotenv import load_dotenv
load_dotenv()

import os
import requests
from tavily import TavilyClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage



@tool
def get_weather(city: str) -> str:
    """
    Fetches the current weather information for a specified city.
    Use this tool whenever the user asks for temperature, conditions, or forecasts of a location.
    """

    api_key = os.getenv("open_weather_apikey")
    if not api_key:
        return "Error: Missing open_weather_apikey in .env file."

    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"The current weather in {city} is {temp}°C with {desc}."
        return f"Could not retrieve weather for {city}. Error: {data.get('message')}"
    except Exception as e:
        return f"An error occurred: {str(e)}"



@tool
def get_city_news(city: str) -> str:
    """
    Fetches the latest news headlines for a specified city.
    Use this tool whenever the user asks for news, headlines, or recent events in a city.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: Missing TAVILY_API_KEY in .env file."

    try:
        client = TavilyClient(api_key=api_key)
        results = client.search(
            query=f"latest news in {city}",
            topic="news",
            days=7,
            max_results=5,
        )

        articles = results.get("results", [])
        if not articles:
            return f"No recent news found for {city}."

        lines = [f"Latest news in {city}:"]
        for i, item in enumerate(articles, start=1):
            title = item.get("title", "No title")
            snippet = (item.get("content") or "")[:200]
            url = item.get("url", "")
            lines.append(f"{i}. {title}\n   {snippet}\n   {url}")
        return "\n".join(lines)
    except Exception as e:
        return f"An error occurred while fetching news: {str(e)}"



llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
tools_list = [get_weather, get_city_news]
tools_map = {t.name: t for t in tools_list}
llm_with_tools = llm.bind_tools(tools_list)


def get_text(content) -> str:
    """Newer Gemini wrappers may return content as a list of parts."""
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict) and part.get("type") == "text":
            parts.append(part["text"])
    return "".join(parts)



def chat_turn(messages: list, max_steps: int = 5) -> str:
    for _ in range(max_steps):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        
        if not response.tool_calls:
            return get_text(response.content)

        for tool_call in response.tool_calls:
            name = tool_call["name"]
            print(f"   (using tool: {name} -> {tool_call['args']})")

            if name in tools_map:
                output = tools_map[name].invoke(tool_call["args"])
            else:
                output = f"Unknown tool: {name}"

            messages.append(
                ToolMessage(content=str(output), tool_call_id=tool_call["id"])
            )

    return "Sorry, I couldn't finish that request."



if __name__ == "__main__":
    messages = [
        SystemMessage(
            content=(
                "You are a friendly, helpful assistant. Chat naturally with the user. "
                "When they ask about weather in a city, use the get_weather tool. "
                "When they ask about news in a city, use the get_city_news tool. "
                "For anything else, just answer normally. Keep replies short and clear."
            )
        )
    ]

    print("Chat with the assistant. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Bye!")
            break

        messages.append(HumanMessage(content=user_input))
        reply = chat_turn(messages)
        print(f"\nAssistant: {reply}\n")