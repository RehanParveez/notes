from __future__ import annotations
from pathlib import Path

DEFAULT_INSTRUCTIONS = (
  "You are updating one section of a developer's living project notes.\n"
  "Update ONLY this section to reflect the code change shown in the diff below.\n"
  "Preserve the existing structure and any content not affected by this diff.\n"
  "Return ONLY the replacement content for this section — no commentary, "
  "no markdown code fences, no explanation."
)

def load_instructions(template_path: str | Path | None = None) -> str:
  if template_path and Path(template_path).exists():
    return Path(template_path).read_text(encoding="utf-8").strip()
  return DEFAULT_INSTRUCTIONS

def build_prompt(diff: str, current_section: str, template_path: str | Path | None = None) -> str:
  instructions = load_instructions(template_path)
  section_display = current_section.strip() if current_section.strip() else "(empty — this is a new section)"
  return (
    f"{instructions}\n\n"
    f"--- Current section content ---\n{section_display}\n\n"
    f"--- Diff of the code change ---\n{diff}\n\n"
    f"--- Updated section content ---\n"
  )