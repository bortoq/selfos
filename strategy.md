# Strategy

## Positioning

Self OS is a delegation system that runs on GitHub.  
It learns from your activity and gradually automates routine tasks.

## Core Loop

**Observe → Suggest → Trust → Delegate**

Suggestions are made through GitHub Issues.  
After enough successful reviews, actions can be performed automatically.

## Why GitHub for Phase 0

- Storage, execution, and user interface are already available
- Delegation feels natural (Issues = suggestions)
- Users already have accounts and understand the mechanics
- No infrastructure costs

## Delegation Approach

- All actions start in **review mode** (Issue is created)
- User accepts or corrects the suggestion
- Trust level increases with each accepted suggestion
- When the threshold is reached, the system offers **auto mode** (direct commits)

## Focus in Phase 0

- Build the Delegation Engine first
- Use Event Categorization as the primary example
- Make diagnostics visible in README
- Keep everything simple and local to the repository

## Long-term Direction

After Phase 0, the system can expand beyond GitHub while keeping the same delegation principles.