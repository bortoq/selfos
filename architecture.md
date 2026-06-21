# Architecture

## Overview

Self OS Phase 0 is built entirely on GitHub.  
The repository acts as both storage and execution environment.

## Main Components

### Activity Log
- Stored as JSON files in `data/activity/`
- Populated by GitHub Actions

### Delegation Engine
- Implemented through GitHub Actions
- Creates **Issues** with suggestions
- Tracks trust level per action type
- Can switch to automatic commits when trust threshold is reached

### Diagnostics Dashboard
- The `README.md` serves as the main dashboard
- Shows daily statistics, category distribution, and a simple Life Management Score
- Always visible and up-to-date

### Data Sources
- GitHub Activity (native)
- Calendar
- Notes/tasks export (up to 3 sources total)

### Delegation Flow
1. New event appears in Activity Log
2. Action analyzes it and creates an Issue with a suggestion
3. User accepts, edits, or rejects via GitHub
4. Trust counter increases
5. After enough acceptances → auto mode becomes available

## Repository Structure

```
selfos-data/
├── data/activity/         # JSON logs
├── .github/workflows/     # Delegation logic
├── README.md              # Diagnostics + public profile
└── selfos.yaml            # Configuration
```

## Key Advantages of This Approach
- No separate server or database needed
- Natural delegation mechanism using Issues and PRs
- Full data ownership
- Fast to develop and deploy