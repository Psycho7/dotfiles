---
name: relayed-diagnosis-mode
description: Enter relayed diagnosis mode, for diagnosing an environment the agent cannot access while the user runs probes there and reports back.
argument-hint: [symptom]
disable-model-invocation: true
---

# Relayed Diagnosis Mode

You cannot reach the target environment; the user relays probes and results. Local code, docs, and history are your only direct sources. These rules hold across turns until the mode ends.

Symptom: $ARGUMENTS

## Lifecycle

- **Enter**: open the reply with the quoted line `> 🟢 **RELAYED DIAGNOSIS MODE · ACTIVE**`, then Scope.
- **Exit**: the user ends the mode or moves to another task (e.g. "now fix it"). Open the reply with the quoted line `> 🔴 **RELAYED DIAGNOSIS MODE · ENDED**`. A verdict does not exit.

## Scope (before any probe)

1. Explore code, docs, and issue history for the symptom, and trace the path it runs through end to end. Don't narrow the search to what changed; "it worked before" may be wrong.
2. Ask until the symptom is concrete: what is observed, where, expected vs actual, since when, what changed.
3. Confirm the target environment in one line (OS, shell/tools, runtime, deployed version), stating what you inferred from the repo, unless the user's prompt already states it.
4. Probe only after the symptom is concrete and the environment is confirmed.

## Each round

1. Answer what the codebase can before asking; ask only for runtime facts.
2. Send one small probe batch, then stop.
3. On results: one or two lines on what is established or ruled out, then the next batch. At the root cause, give the evidence chain.

## Probes

- Assume hand-typed transfer both ways unless told pasting works. Short commands; answers as yes/no, a number, an enum, or one short value. With paste, filtered output of one to three lines is fine.
- Batch only probes that are independent and serve the same question. A probe that depends on another's result waits for the next round.
- Name the tool or shell and where to run it (host, DB, connection) when not obvious.
- Read-only by default. Propose a write or config change only when no read-only probe can answer the question, or it saves at least 3 rounds net of its own (apply, verify, revert). Propose a restart only when no read-only probe can answer. State the estimate, flag it, and wait for approval.

## Rules

- Don't explain what possible answers would mean before they arrive. Skip what an experienced developer already knows. Cite `file:line` only when the link isn't obvious.
- One hypothesis per probe; when results don't fit, gather data instead of guessing. On "stop guessing", fall back to established evidence.
- When a result contradicts an established fact, say so; don't explain it away. The next round is only a cross-check: suspect the probe first (wrong host/DB, transcription), then check whichever side is cheaper. If the fact falls, drop everything concluded from it. If both sides hold, stop probing, list established and ruled-out facts, and ask how to proceed.
- After three rounds that establish or rule out nothing, stop, list established and ruled-out facts, and ask how to proceed.
- If local code may differ from the deployed build, say so once.
- Stop at the root cause or the user's boundary. No fixes or docs unless asked.
