# 🌾 Farmer Advisory Bot

An AI-powered chatbot that helps farmers with weather-based advice, local news, crop prices, pest and disease alerts, and farming tips. It runs as a simple web app built with Streamlit.

## Features

- Chat with an AI advisor that remembers the conversation
- **Live weather** for any city using the OpenWeather API
- **Local news and farming information** (crop prices, pests, schemes) using Tavily search
- **Crop photo upload**: share a leaf or plant photo and get likely causes and next steps
- Replies in **English, Hindi or Punjabi**
- Sidebar to set location and main crop
- Quick buttons for common questions

## Tech Stack

- Python
- Streamlit (web UI)
- LangChain with Google Gemini (language model and tool calling)
- OpenWeather API (weather)
- Tavily API (news and web search)

## Project Structure

```
.
├── Agents.py
├── farmer_bot_ui.py    # Streamlit web app
├── chat_agent.py       # Terminal version of the chatbot
├── .env                # create your own (to store API keys)
├── requirements.txt
└── README.md
```

## Setup

### 1. Install the packages

```
pip install streamlit langchain-google-genai langchain-core python-dotenv requests tavily-python
```

### 2. Get your API keys

| Service | Where to get it | Cost |
|---|---|---|
| Google Gemini | Google AI Studio | Free tier available |
| OpenWeather | openweathermap.org | Free plan available |
| Tavily | tavily.com | Free tier available |

New OpenWeather keys can take 1 to 2 hours to activate.

### 3. Create a `.env` file

Create a file named `.env` in the project folder:

```
GOOGLE_API_KEY=your_gemini_key_here
open_weather_apikey=your_openweather_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Use no quotes and no spaces around the `=` sign.

### 4. Run the app

Web app:

```
streamlit run farmer_bot_ui.py
```

Terminal version:

```
python chat_agent.py
```

## Example Questions

- Should I irrigate my wheat today?
- Is it safe to spray pesticide this week?
- What is the current mandi price of wheat in Punjab?
- Are there any pest alerts for cotton near me?
- How do I apply for PM-Kisan?
- Upload a leaf photo and ask: "What is wrong with this plant?"

## How It Works

1. The user sends a message in the chat.
2. The Gemini model decides whether to answer directly or call a tool.
3. Tools available: `get_weather`, `get_city_news`, `search_farm_info`.
4. The model reads the tool results and writes a simple, practical answer.

## Troubleshooting

| Problem | Fix |
|---|---|
| "Missing API key" error | Check that the name in `.env` matches the name in the code exactly |
| Weather returns 401 error | The OpenWeather key is not active yet, or is wrong |
| "Model not found" error | Change the model name in the `ChatGoogleGenerativeAI(...)` line |
| Tavily `days` error | Replace `days=7` with `time_range="week"` |
| Image upload fails | The selected model may not support images |

## Security

- Never upload your `.env` file to GitHub. Add `.env` to your `.gitignore`.
- If you ever share a key by mistake, regenerate it right away.

## Limitations

- Advice comes from an AI model and web search, so it can be wrong. Confirm important decisions, such as spraying or selling, with a local agriculture officer.
- Photo analysis is a general guess, not a trained disease detector.

## Future Improvements

- Connect a trained plant disease detection model (CNN) for leaf photos
- 5-day weather forecast for better irrigation planning
- Voice input for farmers
- SMS or WhatsApp alerts

## Author

Khayati Sharma
