"""Prompt engineering and template generation for StudySloth AI study aids.
Designed to elicit high-quality, structured outputs from open-weight local LLMs.
"""

from typing import Dict, Any

SYSTEM_INSTRUCTION = """You are StudySloth AI, a patient, thorough, and encouraging study assistant.
Your philosophy is "Slow and Steady": deep comprehension, structured clarity, and zero fluff.
Always ground your answers strictly in the provided study notes.
Do not hallucinate facts outside the material. If the material does not mention something, do not invent it.
Format your responses using clean GitHub-flavored markdown.
"""

PROMPT_TEMPLATES = {
    "summary": """Based ONLY on the provided study notes below, write a comprehensive yet clear study summary.

Structure your response as follows:
## 🦥 Executive Summary
A concise 2-3 paragraph overview capturing the fundamental essence of the topic.

## 🎯 Core Themes & Mechanics
Explain the primary ideas, how they connect, and the underlying logic or mechanisms.

## 💡 Big Picture Takeaway
A 1-2 sentence memorable takeaway for rapid recall.

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
""",

    "key_points": """Based ONLY on the provided study notes below, extract the most critical key points and takeaways.

Structure your response as follows:
## 📌 High-Yield Key Points
- Group points logically with bold headings if multiple subtopics exist.
- Use clear bullet points with key concepts in **bold**.
- Prioritize high-impact exam-relevant insights over trivia.

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
""",

    "definitions": """Based ONLY on the provided study notes below, compile a comprehensive glossary of terms and definitions.

Structure your response as follows:
## 📖 Key Terminology & Definitions

For each term found in the text, use this format:
- **[Term]**: [Clear, unambiguous definition based on the notes]
  *Context/Application*: [How or where this term applies in the material]

List at least 5 to 10 key terms if present in the text.

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
""",

    "flashcards": """Based ONLY on the provided study notes below, generate high-yield study flashcards for active recall.

Provide 5 to 8 flashcards. Each card must have a focused Question and a concise Answer.

Format each card cleanly as:
### Flashcard [Number]
**Q**: [Focused question testing a single concept]
**A**: [Accurate, concise answer grounded in the notes]

---

At the end of your response, provide the exact same cards inside a single valid JSON block for export:
```json
[
  {{"id": 1, "question": "...", "answer": "..."}}
]
```

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
""",

    "quiz": """Based ONLY on the provided study notes below, generate a 4-to-6 question multiple-choice quiz to test comprehension.

For each question:
1. Provide a clear question stem.
2. Provide exactly four options: A), B), C), and D).
3. State the correct answer clearly.
4. Provide a brief explanation of why the correct answer is right and why distractors are wrong.

Format each question as:
### Question [Number]
[Question stem]
- A) [Option A]
- B) [Option B]
- C) [Option C]
- D) [Option D]

**Correct Answer**: [Letter]
**Explanation**: [Why this is correct based on the notes]

---

At the end of your response, also provide the questions in a single valid JSON block for interactive testing:
```json
[
  {{
    "id": 1,
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A",
    "explanation": "..."
  }}
]
```

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
""",

    "comprehensive": """Based ONLY on the provided study notes below, compile a complete "Slow & Steady" Comprehensive Study Pack.

Include the following sections in order:
1. # 🦥 Comprehensive Study Pack
2. ## 1. Executive Summary
3. ## 2. Core Takeaways & High-Yield Points
4. ## 3. Essential Glossary & Definitions
5. ## 4. Active Recall Flashcards (Q&A)
6. ## 5. Practice Quiz (Questions with Answer Key & Explanations)

Make sure every section is thoroughly detailed, encouraging, and accurate to the notes.

STUDY NOTES:
\"\"\"
{notes}
\"\"\"
"""
}


def build_prompt(output_type: str, notes: str) -> str:
    """Builds the formatted user prompt based on requested study aid output."""
    template = PROMPT_TEMPLATES.get(output_type, PROMPT_TEMPLATES["summary"])
    return template.format(notes=notes)
