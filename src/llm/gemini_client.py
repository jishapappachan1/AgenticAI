"""Gemini-backed implementation of the LLM interface."""

import google.generativeai as genai

from src.llm.base import LLMClient


class GeminiClient(LLMClient):
    """Thin adapter around Gemini so app code remains provider-agnostic."""

    def __init__(self, api_key: str, model_name: str) -> None:
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY. Add it to your environment or .env file.")
        genai.configure(api_key=api_key)
        resolved_model = self._resolve_model_name(model_name)
        self.model_name = resolved_model
        self._model = genai.GenerativeModel(resolved_model)

    def _resolve_model_name(self, requested_model: str) -> str:
        """
        Resolve a generateContent-capable model from available Gemini models.

        Why this exists:
        - Avoids hard failures when a configured model is unavailable for the API version/key.
        - Keeps the MVP resilient without asking beginners to debug model catalog issues.
        """
        fallback_candidates = [
            requested_model,
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
        ]

        try:
            available_models: list[str] = []
            for model in genai.list_models():
                if "generateContent" not in getattr(model, "supported_generation_methods", []):
                    continue
                name = getattr(model, "name", "")
                if name.startswith("models/"):
                    name = name.split("/", maxsplit=1)[1]
                if name:
                    available_models.append(name)

            for candidate in fallback_candidates:
                if candidate in available_models:
                    return candidate

            if available_models:
                return available_models[0]
        except Exception:
            # Fallback to requested model if listing fails; generation call will surface exact error.
            pass

        return requested_model

    def generate(self, prompt: str) -> str:
        response = self._model.generate_content(prompt)
        return response.text or ""
