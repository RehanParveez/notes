from notes.mapping import MappingResolver
from notes.diff_extractor import unified_diff
from notes.prompt_builder import build_prompt
from notes.llm_client import generate

old_content = """def calculate_yield(base, factor):
  return base * factor
"""

new_content = """def calculate_yield(base, factor):
  adjusted = base * factor
  return adjusted
"""
file_path = "apps/inventory/models.py"

resolver = MappingResolver("notes-map.yml")
mapping = resolver.resolve(file_path)

if mapping is None:
  raise RuntimeError(f"No mapping found for {file_path}")

notes_file, section = mapping

diff = unified_diff(
  old_content,
  new_content,
  file_path,
)

current_section = (
  "The `calculate_yield` function returns the base value multiplied "
  "directly by the factor."
)

prompt = build_prompt(
  diff=diff,
  current_section=current_section,
  template_path="prompt_template.txt",
)

print(f"Notes file: {notes_file}")
print(f"Section: {section}")
print("\nSending prompt to Ollama...\n")

response = generate(prompt)

print("--- Ollama response ---")
print(response)