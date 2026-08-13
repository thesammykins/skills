# Amp adapter

Amp schedules resume the current thread with its saved prompt and history. Before scheduling, load the `building-schedules` skill and make the saved prompt self-contained: include the monitor contract, source, state location, decision logic, delivery expectation, expiry, and exact report format.

- Use Amp schedule management to create, inspect, update, pause, resume, and remove the schedule. Read the schedule back after every change.
- A scheduled thread report is not an external notification. Ask before adding a webhook, chat destination, or other audience.
- Keep checkpoints in durable state outside the thread transcript when restart/replay correctness matters. Thread history is context, not an atomic event store.
- For a bounded deployment watch, set an explicit end condition and remove the schedule when it is met.
