"""
Hugging Face integration for ASET
Connects the project to Hugging Face inference endpoints or transformers models.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("huggingface_integration")
logging.basicConfig(level=logging.INFO)


class HuggingFaceClient:
    """
    Minimal Hugging Face client wrapper compatible with transformers or HF inference
    APIs.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model_name = model_name or os.getenv("HF_MODEL_NAME", "microsoft/DialoGPT-medium")
        self.api_token = api_token or os.getenv("HF_TOKEN")
        self.base_url = base_url or os.getenv("HF_API_BASE_URL", "https://api-inference.huggingface.co/models")
        self.headers = {}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"

    def generate_text(self, prompt: str, max_new_tokens: int = 250, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Simulated generation for local prototype use.
        Replace with actual HF API calls when endpoint and token are ready.
        """
        result = {
            "model": self.model_name,
            "prompt": prompt,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "status": "simulated",
            "output": {
                "text": f"[HF Simulation] Model '{self.model_name}' would respond to: {prompt}",
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
            },
        }
        return result

    def chat_completion(self, messages: List[Dict[str, str]], max_new_tokens: int = 250) -> Dict[str, Any]:
        """
        Orchestrates a chat-style request using the supplied message history.
        """
        last_user_message = ""
        for message in messages:
            if message.get("role") == "user":
                last_user_message = message.get("content", "")

        if not last_user_message:
            return {"status": "error", "message": "No user prompt found"}

        return self.generate_text(last_user_message, max_new_tokens=max_new_tokens)


class ASETHuggingFaceBridge:
    """
    High-level bridge between ASET project tasks and Hugging Face models.
    """

    def __init__(self, model_name: Optional[str] = None, api_token: Optional[str] = None):
        self.client = HuggingFaceClient(model_name=model_name, api_token=api_token)

    def create_project_plan(self, project_name: str, project_type: str, description: str) -> Dict[str, Any]:
        prompt = f"Create a project plan for {project_name}, a {project_type} project. Description: {description}."
        return self.client.generate_text(prompt)


if __name__ == "__main__":
    bridge = ASETHuggingFaceBridge(model_name="microsoft/DialoGPT-medium")
    result = bridge.create_project_plan(
        "ASET",
        "web",
        "Open-source AI-enabled project generator"
    )
    print(json.dumps(result, indent=2))
