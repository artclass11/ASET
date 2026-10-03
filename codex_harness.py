"""
Codex Harness Integration for ASET
Provides a simple project orchestration interface for ChatGPT/Astra workflows.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("codex_harness")


class CodexHarness:
    """
    Lightweight Codex-style harness wrapper for project generation.
    This class can be used as the orchestration layer for model-backed automation.
    """

    def __init__(self, model_name: str = "astra-opensource", base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url or os.getenv("ASTRA_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("ASTRA_API_KEY")
        self.session_id = f"codex-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.history: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def build_prompt(self, task_description: str, project_context: Optional[Dict[str, Any]] = None) -> str:
        context = ""
        if project_context:
            context = json.dumps(project_context, indent=2)
        return f"""
You are a senior software engineer and project architect.
Task: {task_description}

Project Context:
{context}

Provide a clear technical plan, file structure, and implementation steps.
"""

    def simulate_response(self, task_description: str, project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Local simulator for harness behavior when no live model is connected.
        """
        prompt = self.build_prompt(task_description, project_context)
        self.add_message("user", prompt)

        response = {
            "session_id": self.session_id,
            "model": self.model_name,
            "status": "simulated",
            "output": {
                "summary": f"Project plan generated for: {task_description}",
                "steps": [
                    "Analyze requirements",
                    "Define architecture",
                    "Create project skeleton",
                    "Set up dependencies",
                    "Generate initial code",
                    "Validate configuration"
                ],
                "project_context": project_context or {},
                "prompt": prompt
            },
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        self.add_message("assistant", json.dumps(response["output"]))
        return response

    def run_task(self, task_description: str, project_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run the codex harness task.
        If a real model endpoint is configured, this could call the remote API.
        """
        logger.info("Running codex task: %s", task_description)
        return self.simulate_response(task_description, project_context)


if __name__ == "__main__":
    harness = CodexHarness(model_name="astra-opensource")
    result = harness.run_task(
        "Build an AI project generator web app",
        {
            "project_name": "ASET",
            "project_type": "web",
            "description": "Open-source AI-enabled project generator",
            "tech_stack": ["FastAPI", "React", "PostgreSQL"]
        }
    )
    print(json.dumps(result, indent=2))
