# Architecture

## Overview

Self OS is a modular personal operating environment with local-first data, lightweight check-ins, sprint management, reflection, analytics, AI guidance, and an optional public profile.

## Components

- Local Data Store: JSON files containing metrics, check-ins, sprints, journal entries, tasks, notes, and configuration.
- Check-in Module: morning and evening prompts through CLI or web.
- Sprint Module: creates, tracks, and closes short planning cycles with goals and retrospectives.
- Journal Module: private free-form text or voice-derived notes for context and reflection.
- Analytics Module: aggregates metrics and highlights trends or correlations.
- Integration Module: imports signals from tools such as GitHub, calendars, RescueTime-like activity sources, and sleep trackers.
- AI Advisor: asks adaptive questions, structures raw notes, suggests interpretations, and drafts retrospectives.
- Public Profile Generator: converts selected local data into a static profile site.
- Web Dashboard: dashboard, graphs, sprint views, and reports.
- CLI Surface: fast commands for capture and review.

## Data Flow

1. The user completes a morning or evening check-in.
2. The system stores responses in local JSON files.
3. External integrations optionally import passive data.
4. Analytics aggregate recent metrics, streaks, and sprint progress.
5. The AI advisor uses current and historical data to ask better questions and draft useful summaries.
6. Sprint reviews update goals and next actions.
7. Selected data can be exported into a public profile.

## Key Design Rule

The system should feel like a low-friction operating loop, not like a form-heavy tracker. Reflection and planning must stay short, structured, and repeatable.

## Privacy Rule

Private by default. Public sharing is explicit. The user owns the source data and should be able to keep the full system local.
