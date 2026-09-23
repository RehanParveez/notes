# notes

It's a background tool that watches your projects as you code and keeps a matching set of markdown notes updated automatically, so there is no manual note-taking, no stale context.

## What it is?

The moment you save a file with new or changed logic, the matching notes file updates itself, and gets positioned exactly where the change happened. This can work across as many projects as you register with it.

## How it works?

- Watches your registered project folders for file saves
- Diffs the change against the last known version of that file
- Sends just that diff to a local AI model (Ollama — free, runs on your machine, no internet needed)
- Patches only the matching section of that file's notes — everything else stays untouched
- Remembers everything (snapshots, notes index, lessons) in one local SQLite database, so a project you haven't opened in months is still fully retrievable

## Requirements
- Python 3.11+
- Ollama, with a model pulled locally (`qwen2.5-coder`)