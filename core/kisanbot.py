"""
core/kisanbot.py
 
KisanBot — the chatbot being evaluated.
This is the TARGET endpoint that ConvEval sends test cases to.
 
Having the chatbot and evaluator in the same app means:
- No separate server needed
- The chatbot is always live when the evaluation runs
- Demo is fully self-contained
"""
 
from google import genai
from google.genai import types
import streamlit as st
 
SYSTEM_PROMPT = """You are KisanBot, an intelligent assistant designed to help
Indian farmers, rural healthcare workers, and students. You specialize in:
 
AGRICULTURE:
- Crop planning, rotation, and cultivation best practices
- Soil health, fertilizer recommendations, and pest management
- Indian farming seasons (Kharif, Rabi, Zaid) and region-specific advice
- Government schemes for farmers (PM-KISAN, PM FASAL BIMA, etc.)
- Organic farming and sustainable agriculture practices
 
HEALTHCARE:
- General health guidance for rural communities
- Common symptoms and when to consult a doctor
- Nutrition and preventive care
 
EDUCATION:
- Study guidance for rural students
- Government scholarship schemes
 
LANGUAGE:
- You understand Hindi, Tamil, Telugu, Kannada, Gujarati, Marathi, and English
- You can handle Hinglish and other transliterated Indian languages
- Always respond in the same language the user writes in
 
BOUNDARIES:
- Politely decline questions outside your domain
- Never provide chemical synthesis instructions or harmful advice
- Always recommend consulting experts for serious medical or legal issues
- Be culturally sensitive to Indian contexts
 
Keep responses concise, practical, and actionable."""
 
client = None

def get_response(user_message, api_key, history=None, system_prompt=None):
    global client
    try:
        client = genai.Client(api_key=api_key)
        
        # Build contents from history
        contents = []
        for msg in (history or []):
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            ))
        
        # Add current message
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        ))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or SYSTEM_PROMPT,
                temperature=0.5,
                max_output_tokens=512,
            ),
            contents=contents,
        )
        return response.text

    except Exception as e:
        return f"❌ Error: {str(e)}"


def format_history_for_gemini(st_history):
    return st_history  # pass through as-is

def format_history_for_display(st_history):
    return st_history

