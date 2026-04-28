---
description: "Workspace instructions for the glowing-giggle social media crawling dashboard. Use this guidance for general repository context, conventions, and when to ask for missing tooling details."
---

# glowing-giggle Workspace Instructions

## Project overview
- This repository is a dashboard for crawling social media X.
- The only documented project file is `README.md`; no build or test scripts are present in the repository root.

## What to do first
- Inspect existing source files if they are added later.
- If a task requires build, run, or dependency commands and they are not present, ask the user for the intended language/framework or the missing commands.
- Prefer explicit confirmation before introducing assumptions about the runtime environment.

## Recommended agent behavior
- Do not assume Node, Python, Docker, or any specific stack unless the repository contains supporting files like `package.json`, `requirements.txt`, `pyproject.toml`, `Dockerfile`, or similar.
- When asked to create or modify functionality, keep changes minimal and aligned with the project description in `README.md`.
- If the repository structure is incomplete, ask for additional files or clarify the desired architecture before making broad changes.

## Key repository conventions
- There are currently no conventions defined beyond the README description.
- Use `README.md` as the main source of truth until more project documentation appears.

## When to escalate
- If a requested change requires a build/test command, dependency install, or environment setup not documented in the repo.
- If there are multiple possible runtime stacks and the repository does not clearly indicate one.
- If a feature request is broader than the repository's current documented scope.
