---
name: proxy-explore
description: Delegate multi-step code search and codebase exploration to other models. Triggers proactively on broad searches, pattern discovery, structural exploration, and reference tracing.
---

# Delegation

This skill saves tokens by delegating code search and exploration to other token effective models. You are the expensive model. Every file you read, every grep you run, is burning expensive tokens on work that a cheap model can do just as well.

## The Rule

**If a single, trivial tool call answers the question — do it yourself. Otherwise, delegate.**

This is not optional. The reason this skill exists is that reading dozens of files to answer "where is X used?" or "what does the auth module do?" is input-heavy but low-reasoning, on which you can trust cheap and fast models.

## When to Do It Yourself vs. Delegate

**Do it yourself** — only when ANY of these are true:
- You know exactly what to search (exact function name, class, variable)
- A single keyword or pattern suffices
- You already know the file location

**Delegate** — everything else:
- Multiple search angles needed
- Unfamiliar module structure
- Cross-layer or cross-file pattern discovery
- "Find all X", "where is Y used", "what does Z do"
- Exploring project structure or summarizing modules
- Mapping data flows, call chains, or reference graphs
- Any time you're unsure whether 1 call will suffice

If you catch yourself reaching for a second Grep or Glob — stop and delegate instead.

## How to delegate

1. Frame the user's question as a structured exploration prompt
2. Delegate to Agent(zai-explore)

### Prompt Structure

Lead with the user's question as a one-sentence preamble, then structured search sections. Don't mix the task description into the structured fields — they should be pure search parameters.

The quality of delegation depends entirely on the prompt. Avoid vague prompts, be specific about three things:

1. **What to search for** — name the classes, functions, patterns, or concepts explicitly
2. **Where to search** — absolute paths of directories you have verified exist (use Glob if unsure). Never guess.
3. **Scope** — (optional) constrain the search when needed to avoid confusion

Below are good prompt examples:

### Example 1
```
Find how Tokio spawns and schedules tasks on its multi-threaded runtime.

What to search for:
- The `spawn` entry point (both the public `tokio::spawn` function and the internal dispatch)
- The `Shared` struct or worker-stealing logic in the scheduler
- How tasks transition between states (Notified → Running → Idle)

Where to search:
- /tokio/tokio/src/

Scope:
- Focus only on the multi-threaded scheduler, not the current-thread or test
  runtimes. Ignore the `blocking` module and I/O driver. Return the call chain
  from `spawn()` through to the point a worker thread picks up the task.
```

### Example 2
```
Find how Kubernetes validates and admits a new Pod before persisting it to etcd.

What to search for:
- The `Create` handler for the Pod resource in the API server
- Admission webhook invocation chain (the `Admit` / `Validate` interfaces)
- The `Strategy` implementation for Pods in the registry layer

Where to search:
- /kubernetes/pkg/
- /kubernetes/staging/src/k8s.io/apiserver/

Scope:
- Cover only the create path, not update/delete. Ignore scheduler and
  kubelet — stop at the point the object is written to storage.
  Return the function call chain and the files/line numbers involved.
```

### Example 3

```
Find how Next.js resolves a dynamic route segment to its page component
during server-side rendering.

What to search for:
- The route-matcher or route-resolver that maps a URL path to a page module
- The logic that extracts dynamic params (e.g. `[slug]`) from the matched segment
- Where the matched page component is loaded and passed to the RSC renderer

Where to search:
- /next/packages/next/src/

Scope:
- Focus on the App Router (`app/` directory) only, not the Pages Router
  (`pages/` directory). Ignore middleware execution, caching, and static
  generation — trace only the SSR request path from URL to rendered component.
```

## After Receiving Results

The output follows a structured format: **FILES FOUND** (absolute paths + descriptions), **ANSWER** (direct response), and **GAPS** (what couldn't be found). Use this structure to quickly extract what you need.

- Use the output as context for your main task — trust it, and don't repeat the search yourself
- If the GAPS section lists missing areas, refine the prompt and re-delegate for those specific gaps
- Trust the results for file locations and summaries; use tool `Read` to verify only when you need exact code for an edit
- Check the `<analysis>` block at the top of the response — if the **Actual Need** or **Success Looks Like** lines don't match your intent, re-delegate with a clarified prompt rather than using wrong results
- If GLM reports "No results found," verify once with Grep before telling the user — the subagent may lack file permissions that you have
- **Give-up rule:** If GLM returns unhelpful results 3 times for the same query (even after refining the prompt), stop delegating and search yourself.