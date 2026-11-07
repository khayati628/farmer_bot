

from dotenv import load_dotenv
load_dotenv()

import os
import base64
import requests
import streamlit as st
from tavily import TavilyClient

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

st.set_page_config(page_title="Farmer Advisory Bot", page_icon="🌾", layout="centered")



@tool
def get_weather(city: str) -> str:
    """
    Fetches the current weather for a city.
    Use this when the user asks about temperature, rain, conditions or farming weather.
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
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            desc = data["weather"][0]["description"]
            return (
                f"Weather in {city}: {temp}°C, {desc}, "
                f"humidity {humidity}%, wind {wind} m/s."
            )
        return f"Could not retrieve weather for {city}. Error: {data.get('message')}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


@tool
def get_city_news(city: str) -> str:
    """
    Fetches the latest news for a city or region.
    Use this when the user asks for local news or recent events.
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


@tool
def search_farm_info(query: str) -> str:
    """
    Searches the web for farming information: crop prices (mandi rates), pest or
    disease alerts, government schemes, fertilizer advice, sowing and harvest tips.
    Use this for any farming question that is not weather or city news.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: Missing TAVILY_API_KEY in .env file."

    try:
        client = TavilyClient(api_key=api_key)
        results = client.search(query=query, max_results=5)
        articles = results.get("results", [])
        if not articles:
            return "No results found."

        lines = [f"Search results for: {query}"]
        for i, item in enumerate(articles, start=1):
            title = item.get("title", "No title")
            snippet = (item.get("content") or "")[:300]
            url = item.get("url", "")
            lines.append(f"{i}. {title}\n   {snippet}\n   {url}")
        return "\n".join(lines)
    except Exception as e:
        return f"An error occurred during search: {str(e)}"


tools_list = [get_weather, get_city_news, search_farm_info]
tools_map = {t.name: t for t in tools_list}


@st.cache_resource
def load_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    return llm.bind_tools(tools_list)


llm_with_tools = load_llm()


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


def run_turn(history: list, system_text: str, max_steps: int = 5) -> str:
    """Runs the model, executes any tool calls, and returns the final reply."""
    for _ in range(max_steps):
        msgs = [SystemMessage(content=system_text)] + history
        response = llm_with_tools.invoke(msgs)
        history.append(response)

        if not response.tool_calls:
            return get_text(response.content)

        for tool_call in response.tool_calls:
            name = tool_call["name"]
            if name in tools_map:
                output = tools_map[name].invoke(tool_call["args"])
            else:
                output = f"Unknown tool: {name}"
            history.append(
                ToolMessage(content=str(output), tool_call_id=tool_call["id"])
            )

    return "Sorry, I couldn't finish that request. Please try again."



if "chat" not in st.session_state:
    st.session_state.chat = []        
if "history" not in st.session_state:
    st.session_state.history = []     
if "sent_image" not in st.session_state:
    st.session_state.sent_image = None




with st.sidebar:
    st.header("🌾 Your farm")
    location = st.text_input("Location (city or district)", value="Gurdaspur")
    crop = st.selectbox(
        "Main crop",
        ["Wheat", "Rice (Paddy)", "Maize", "Cotton", "Sugarcane", "Potato",
         "Tomato", "Mustard", "Other"],
    )
    language = st.selectbox("Reply language", ["English", "Hindi", "Punjabi"])

    st.divider()
    st.subheader("Quick questions")
    quick = None
    if st.button("🌦️ Weather advice for today", use_container_width=True):
        quick = (
            f"Check the weather in {location} and tell me what I should do "
            f"on my {crop} farm today."
        )
    if st.button("📰 Farming news near me", use_container_width=True):
        quick = f"Find the latest news near {location} that matters to {crop} farmers."
    if st.button("💰 Market price & tips", use_container_width=True):
        quick = f"What are the current market prices and good practices for {crop} near {location}?"
    if st.button("🐛 Pest & disease alerts", use_container_width=True):
        quick = f"Are there any current pest or disease alerts for {crop} near {location}?"

    st.divider()
    st.subheader("Crop photo (optional)")
    uploaded = st.file_uploader(
        "Upload a leaf or crop photo", type=["jpg", "jpeg", "png"]
    )

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.chat = []
        st.session_state.history = []
        st.session_state.sent_image = None
        st.rerun()



st.title("🌾 Farmer Advisory Bot")
st.caption("Ask about weather, crop care, pests, prices and local news.")

system_text = (
    "You are a friendly farming advisor helping a farmer. "
    f"The farmer is located in {location} and mainly grows {crop}. "
    f"Always reply in {language}, using simple and clear words. "
    "Use get_weather for weather, get_city_news for local news, and "
    "search_farm_info for crop prices, pests, diseases, schemes and farming tips. "
    "Give practical, step-by-step advice, and say clearly when you are not sure. "
    "If a photo is shared, describe what you see on the plant and suggest likely causes "
    "and next steps, and recommend visiting a local agriculture officer for confirmation."
)


for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=250)
        st.markdown(msg["content"])


typed = st.chat_input("Ask your farming question...")
prompt = typed or quick

if prompt:
    
    image_bytes = None
    image_mime = None
    if uploaded is not None:
        image_key = f"{uploaded.name}-{uploaded.size}"
        if st.session_state.sent_image != image_key:
            image_bytes = uploaded.getvalue()
            image_mime = uploaded.type or "image/jpeg"
            st.session_state.sent_image = image_key

    
    st.session_state.chat.append(
        {"role": "user", "content": prompt, "image": image_bytes}
    )
    with st.chat_message("user"):
        if image_bytes:
            st.image(image_bytes, width=250)
        st.markdown(prompt)

    
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image_mime};base64,{b64}"},
            },
        ]
        st.session_state.history.append(HumanMessage(content=content))
    else:
        st.session_state.history.append(HumanMessage(content=prompt))

    
    with st.chat_message("assistant"):
        with st.spinner("Checking weather and searching..."):
            try:
                reply = run_turn(st.session_state.history, system_text)
            except Exception as e:
                reply = f"Something went wrong: {e}"
        st.markdown(reply)

    st.session_state.chat.append({"role": "assistant", "content": reply})