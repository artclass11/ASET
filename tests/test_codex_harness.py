from codex_harness import CodexHarness


def test_build_prompt_includes_task_and_context() -> None:
    harness = CodexHarness()
    prompt = harness.build_prompt("Create a research endpoint", {"version": "v1"})

    assert "Create a research endpoint" in prompt
    assert '"version": "v1"' in prompt


def test_simulate_response_records_conversation() -> None:
    harness = CodexHarness()
    result = harness.run_task("Validate provider data")

    assert result["status"] == "simulated"
    assert result["output"]["summary"] == "Project plan generated for: Validate provider data"
    assert len(harness.history) == 2
