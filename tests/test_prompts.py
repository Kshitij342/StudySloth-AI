"""Tests for prompt generation and templates."""

import pytest
from utils.prompts import (
    PROMPT_TEMPLATES,
    SYSTEM_INSTRUCTION,
    build_prompt,
)


def test_system_instruction_contains_core_principles():
    assert "StudySloth AI" in SYSTEM_INSTRUCTION
    assert "Slow and Steady" in SYSTEM_INSTRUCTION
    assert "Do not hallucinate" in SYSTEM_INSTRUCTION


@pytest.mark.parametrize("output_type", [
    "summary",
    "key_points",
    "definitions",
    "flashcards",
    "quiz",
    "comprehensive",
])
def test_build_prompt_all_types(output_type):
    sample_notes = "Photosynthesis occurs in chloroplasts. Chlorophyll absorbs sunlight."
    prompt = build_prompt(output_type, sample_notes)
    assert sample_notes in prompt
    assert len(prompt) > len(sample_notes)


def test_build_prompt_default_fallback():
    sample_notes = "Binary search runs in O(log n) time."
    prompt = build_prompt("unknown_type", sample_notes)
    # Should fall back to summary template
    assert "Executive Summary" in prompt
    assert sample_notes in prompt


def test_flashcard_prompt_specifies_json():
    prompt = build_prompt("flashcards", "Sample text here.")
    assert "json" in prompt.lower()
    assert "Flashcard" in prompt


def test_quiz_prompt_specifies_options_and_json():
    prompt = build_prompt("quiz", "Sample text here.")
    assert "A)" in prompt
    assert "B)" in prompt
    assert "C)" in prompt
    assert "D)" in prompt
    assert "Correct Answer" in prompt
    assert "json" in prompt.lower()
