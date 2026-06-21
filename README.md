# Self OS

Self OS is a personal control panel that runs on GitHub.  
It aggregates your activity and gradually takes over routine tasks through trusted delegation.

## Core Idea

Self OS follows one loop:

**Observe → Suggest → Trust → Delegate**

Everything happens inside your own GitHub repository. The system collects data, suggests actions through Issues, and after you accept enough suggestions, it can perform actions automatically.

## How It Works

- Your data lives in a GitHub repository (`selfos-data`).
- GitHub Actions import logs and analyze activity.
- Suggestions appear as **Issues**.
- You review and accept or correct them.
- After reaching a trust threshold, actions can run automatically (commits).

This approach gives you full ownership of your data while allowing progressive automation.

## Phase 0 Focus

- Activity Log stored in your repository
- Event categorization as the main delegation example
- Diagnostics visible in README.md
- Delegation through GitHub Issues and Pull Requests
- No separate web application needed

## Long-term Vision

Over time Self OS can become your main interface for managing digital life — all while staying inside a system you already use and fully control.