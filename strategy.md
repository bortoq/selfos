# Strategy

## Positioning

Self is a personal operating system: a private-first tool for managing life as a project. It should not become a social feed, habit game, or generic notes app.

The core promise is:

`Check in -> measure -> plan -> execute -> reflect -> improve`

The public profile is optional. When used, it should show progress and current work, closer to a GitHub profile than to a social media timeline.

## Naming

The project can start as `Self`.

Other names considered:

- `Me OS`: short and personal, but less clear when spoken.
- `Person OS`: descriptive, but colder and less memorable.
- `Self OS`: stronger for the mature platform stage.

Recommended path: use `Self` for the early product and describe it as `personal operating system`. Keep `Self OS` available for the broader platform.

## Competitor Lessons

- Facebook grew from profiles to feeds to an attention market. Self should avoid measuring success by time spent in the product.
- GitHub grew from code hosting to a public professional profile. Self can use the same public-progress pattern for life projects.
- Telegram grew from messenger to ecosystem. Self should not start as an ecosystem, but should keep an API/plugin direction open.
- Notion grew from notes to modular workspace. Self should keep unused modules hidden and let the user enable only what they need.
- Duolingo proves that competition and streaks work, but Self should avoid RPG-style gamification as the main identity.

## Competitor Map

| Project | Strength | Gap Self Targets |
| --- | --- | --- |
| Exist.io | Passive data aggregation and correlations | Weak active planning and sprint loop |
| Gyroscope | Polished life dashboard | More observation than operational control |
| Habitica | Motivation through game mechanics | Too game-like for project-minded users |
| Bearable | Health and symptom tracking | Narrower health focus |
| Day One / Diarly / Journey | Private journaling | No metrics, sprints, or operating loop |
| Medium / blogs | Public writing | Narrative rather than structured progress |
| GitHub Profile | Public progress for code | Mostly limited to software work |
| Notion / Coda / Airtable templates | Flexible manual systems | Too much setup and maintenance |

## Product Risks

- Heavy onboarding can kill the product before the user sees value.
- Manual check-ins can become tedious unless they stay short.
- Public profiles can create fear of judgment if privacy defaults are weak.
- Social features can push the product toward attention-seeking behavior.
- AI advice can become generic unless grounded in real user data.

## Risk Responses

- Onboarding should take about one minute: choose a current project, choose one metric, start the first sprint.
- Check-ins should take about 30 seconds: two to four questions, with optional voice input later.
- Privacy must be default. Publishing is explicit and selective.
- Benchmarks should start with `you now vs you in the past`; cross-user benchmarks come later and must be anonymized.
- Retrospectives should be treated as retention events, not just reports.

## Interface Strategy

The interface is not only screens. It is a command surface.

Commands can come from:

- CLI
- web forms
- voice input
- Telegram bot
- future mobile wrapper

The core should not depend on the input surface. This keeps voice, web, and CLI as adapters around the same product logic.

## Voice Strategy

Early stage:

- voice input through an API such as Whisper or a fast hosted speech model;
- user says a command such as `morning check-in`;
- the system asks questions and stores answers.

Middle stage:

- local speech-to-text where practical;
- text-to-speech through tools such as RHVoice or Edge TTS;
- voice check-ins become a normal input path.

Mature stage:

- full voice navigation for reports and graphs;
- commands such as `show sleep trend for this week`;
- voice becomes one of several first-class interfaces.

## AI Provider Strategy

- DeepSeek Flash or a similar low-cost model is suitable for check-ins, summaries, and retrospective drafts.
- Groq-hosted open models are useful for fast structuring and simple generation where free or cheap tiers are available.
- OpenRouter can reduce provider lock-in by exposing many models through one API.
- Local models through llama.cpp or Ollama can support privacy-first mode for simpler tasks.
- Hybrid routing is preferred: simple structuring locally, deeper retrospective or correlation analysis through stronger hosted models.

## Development Stages

### Self Lite

Goal: one-user working product.

- CLI and simple web UI
- morning and evening check-ins
- local JSON storage
- sprint and retrospective flow
- AI advisor for adaptive questions and retrospective drafts
- static public profile generator
- donation link as the first monetization test

Target: first real user and first dollar.

### Self

Goal: early-adopter product for 100 to 500 users.

- voice input
- GitHub, RescueTime-style, calendar, and basic sleep/activity imports
- `you now vs you in the past` benchmarks
- sprint templates
- customizable public profile
- free plan plus paid plan around $5/month

Target: $100 to $500/month.

### Self OS

Goal: platform stage.

- peer subscriptions to public profiles
- anonymized relative benchmarks
- group and coach workflows
- plugin/API layer
- B2B plans for coaches, therapists, founders, and small teams

Target: $5k to $50k/month before broader platform expansion.

## Market View

Conservative view:

- quantified-self and habit-tracking tools form a large but fragmented market;
- taking even a small share can support a meaningful niche business.

Realistic view:

- likely audience: engineers, founders, quantified-self users, freelancers, ADHD-sensitive users, and people who already think in systems;
- possible paying user conversion: 0.1% of a 10M to 50M reachable audience at around $5/month;
- rough business range: $7M to $36M/year if the category fit is real.

Optimistic view:

- if `personal OS` becomes a recognizable category, the product can expand beyond quantified-self users;
- the broader self-improvement and personal productivity market could grow around this category;
- Self OS would be more like a category creator than a feature app.

## Strategic Boundary

The product must stay an instrument for meaningful work on the self. It should not become a feed, a vanity scoreboard, or an attention-maximizing network.
