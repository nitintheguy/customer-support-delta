"""
Thin wrapper around the Google Gemini API used by every pipeline stage
(classification, reply drafting, judge). Centralizing this makes it easy to
swap models, add retries, or log calls in one place.

Uses the current `google-genai` SDK (the old `google-generativeai` package
is deprecated). Free tier, no credit card required.
Get a free API key at https://aistudio.google.com/apikey

NOTE ON MODEL NAME: Gemini model names get deprecated/replaced fairly often.
As of Sept 2026, "gemini-2.5-flash" was retired for new users in favor of
"gemini-3.6-flash". If this model name also stops working, check
https://ai.google.dev/gemini-api/docs/models for the current free-tier
Flash model and update DEFAULT_MODEL below.
"""

import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None

DEFAULT_MODEL = "gemini-3.6-flash"


def get_client() -> "genai.Client":
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add it to a .env file in the repo root. "
                "Get a free key at https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=api_key)
    return _client


def call_llm_json(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """
    Calls Gemini with a system+user prompt and parses the response as JSON.
    Assumes the system prompt instructs the model to return ONLY JSON, no preamble.
    Raises ValueError if the response can't be parsed as JSON.
    """
    client = get_client()

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config={"system_instruction": system_prompt},
    )

    text = response.text.strip()

    # Strip markdown code fences if the model added them despite instructions
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse Gemini response as JSON: {text!r}") from e