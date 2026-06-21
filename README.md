# Self OS

Self OS is a personal operating environment for running your life like a project: metrics, check-ins, sprints, retrospectives, a private journal, and an optional public progress profile.

## Simple Description

This is not just a diary, planner, or habit tracker. It is a CLI and web product for people who want to manage themselves with minimal friction. The user tracks a few core signals, runs short sprints, reviews outcomes, keeps private notes, and can optionally publish a profile that shows progress rather than attention-seeking content.

## Full Description

Most personal tools are incomplete. Diaries capture narrative but do not create structure. Planners capture tasks but ignore reflection. Quantified-self tools collect metrics but rarely help the user act on them. Social platforms optimize for attention, not progress.

Self OS combines these missing layers into one loop: check-in, measure, plan, execute, reflect, and improve. The product treats a human life more like a long-running project than a stream of posts or reminders.

The user runs short sprints, usually two weeks long, with a goal and a few measurable outcomes. Morning and evening check-ins stay short. External data can be imported from common tools. A private journal adds free-form context. An AI advisor reduces friction by asking adaptive questions, structuring notes, generating sprint retrospectives, and highlighting useful correlations.

The system is private by default. Data belongs to the user. Public sharing is optional and should feel more like a GitHub profile of progress than a social feed.

## Product Principle

User attention is scarce. The product should reduce friction instead of creating new rituals. It should replace vague self-improvement with measurable, reviewable progress.

## Market Context

The idea sits between quantified-self tools, planners, journals, and social profiles.

- Quantified-self products such as Exist.io and Gyroscope are good at observation but weak at active management.
- Habit trackers and gamified tools help consistency but often oversimplify human goals.
- Journals and blogs preserve stories but do not create operational structure.
- GitHub-style public profiles show progress well, but mainly for code.

Self OS combines metrics, sprint structure, reflection, AI-assisted guidance, and optional public profiles into a single system.

## Main Use Cases

- A developer runs a two-week sprint for a product release, tracks focus and overload, and reviews outcomes at the end.
- A language learner tracks study time, retention, and consistency, then compares current progress with their own past baseline.
- A creator keeps private notes, tracks energy and output, and uses AI-generated retrospectives to find bottlenecks.
- A user generates an optional public profile that shows current sprint, recent achievements, and progress trends.
- A user connects external data such as GitHub activity, sleep data, calendar signals, or RescueTime-style productivity sources.

## MVP

- Local JSON-based storage
- CLI commands for check-ins, sprints, and reports
- Morning and evening check-ins
- Sprint creation and retrospective flow
- Private journal entries
- Basic metrics dashboard in a simple web UI
- Static public profile generator
- AI-assisted adaptive questions and sprint summaries

## Similar Projects And Difference

- Exist.io aggregates data and shows correlations, but does not treat life as an actively managed project.
- Gyroscope is visually strong for dashboards, but is closer to observability than operational control.
- Habitica adds motivation through RPG mechanics, but that is not the same as structured self-management.
- Day One and similar journals capture reflection, but not sprint planning or metrics.
- Notion templates can approximate parts of this manually, but lack a dedicated product loop.
- GitHub profiles show progress for developers, but not for life as a whole.

The main difference is the closed loop: metrics, planning, reflection, AI guidance, and optional public progress all live in one product.

## Risks

- Onboarding can be too heavy if the first experience asks too much from the user.
- Manual input can create fatigue and break retention.
- A public profile can create social pressure if privacy defaults are weak.
- The product must avoid becoming another attention-maximizing feed.
- AI advice can become generic noise unless grounded in the user’s own data.

## Monetization

- Paid personal subscription for AI features, integrations, and hosted sync
- Freemium base with local-only mode
- Premium public profile themes and customization
- Team and coach plans for small groups, mentors, or therapists
- Optional hosted benchmark service with anonymized comparisons

## Documents

See [architecture.md](architecture.md), [use-cases.md](use-cases.md), [roadmap.md](roadmap.md), and [demo.md](demo.md).
