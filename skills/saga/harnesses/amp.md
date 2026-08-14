# Amp adapter

Choose an Amp executor before planning: a local runner can use the current checkout and uncommitted state; an orb starts from the project snapshot and cannot see local uncommitted changes. Record that choice and the revision in `SAGA.md`.

- Use Amp subagents only for independent, bounded work. Give each a precise task, owned files, validation command, and durable handoff requirement.
- Use a separate thread or executor when isolation, long-lived work, or a distinct checkout is needed. Keep tightly coupled implementation and integration in the main thread.
- For Amp threads, record a thread URL or durable branch/commit in `PROGRESS.md`; do not rely on display names or transient executor paths.
- Persist saga state in committed files, a durable branch, or another durable store when an orb may be stopped. `~/.sagas` is suitable only when the chosen local environment is persistent.
- Do not ask a worker to push, open a pull request, or alter shared remote state unless the user has authorized that action.
