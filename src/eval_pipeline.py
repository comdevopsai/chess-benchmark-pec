"""
US-2: LLM Evaluation Pipeline (OpenRouter)
Given/When/Then Gherkin Implementation.
"""
import json
import os
from typing import Optional


class OpenRouterClient:
    """Given an OpenRouter API key, When a request is made, Then the LLM responds with assessment + confidence."""

    def __init__(self, api_key: Optional[str] = None, model: str = "inclusionai/ling-3.0-flash:free"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def evaluate_position(self, fen: str, system_prompt: str = "You are a chess evaluation expert.") -> dict:
        """Given a FEN position, When eval_position is called, Then return assessment + confidence."""
        # If no API key, return mock result for testing
        if not self.api_key:
            return {
                "fen": fen,
                "assessment": "draw",
                "confidence": 0.5,
                "model": self.model,
                "mock": True,
            }

        user_message = (
            'Evaluate this chess position and return JSON with '
            '"assessment" (win/draw/loss) and "confidence" (0.0-1.0).'
        )

        try:
            import urllib.request

            payload = json.dumps({
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.1,
                "max_tokens": 200,
            }).encode("utf-8")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com/comdevopsai/chess-benchmark-pec",
                "X-Title": "PEC Position Evaluator",
                "Content-Type": "application/json",
            }

            req = urllib.request.Request(self.base_url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]["message"]["content"]
                return json.loads(choice)
        except Exception as e:
            return {"fen": fen, "error": str(e), "assessment": "unknown", "confidence": 0.0}

    def evaluate_batch(self, positions: list) -> list:
        """Given a batch of FEN positions, When eval_batch is called, Then return list of assessments + confidence scores."""
        results = []
        for fen in positions:
            result = self.evaluate_position(fen)
            results.append(result)
        return results


def format_assessment(result: dict) -> str:
    """Given an evaluation result dict, When format_assessment is called, Then return a readable assessment string."""
    assessment = result.get("assessment", "unknown")
    confidence = result.get("confidence", 0.0)
    fen = result.get("fen", "unknown")
    if assessment == "win":
        return f"[WIN {confidence:.0%}] {fen}"
    elif assessment == "loss":
        return f"[LOSS {confidence:.0%}] {fen}"
    elif assessment == "draw":
        return f"[DRAW {confidence:.0%}] {fen}"
    else:
        return f"[UNKNOWN] {fen}"
