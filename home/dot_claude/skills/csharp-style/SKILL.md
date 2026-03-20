---
name: csharp-style
description: C# code style preferences for writing and refactoring code. Use this skill whenever writing, refactoring, or reviewing C# code in this codebase — especially when composing behaviors, designing APIs, or structuring logic. Also applies when the user asks you to clean up, simplify, or restructure C# code.
---

# C# Code Style Preferences

These are the user's code style preferences for C# development. Follow them when writing new code, refactoring existing code, or suggesting changes.

**Overall philosophy: favor a functional programming style in C#** — pure functions, immutable data, composition over inheritance, expressions over statements. Use the FP features C# provides (LINQ, lambdas, records, pattern matching, switch expressions) as the default approach.

**The code should try to explain itself.** Choose names, structure, and intermediate variables so that someone reading the code can follow the intent without needing external documentation. Named intermediates in pipelines, descriptive method names, and well-chosen types all serve this goal. When something still isn't obvious, that's when a comment earns its place.

## Functional Composition

Favor composing small, focused pieces of logic over building class hierarchies or monolithic methods.

The simplest mechanism that's clear enough wins. A `Func<>` or lambda is often sufficient. Use named delegate types when the lambda signature alone doesn't convey meaning.

```csharp
// Lambda is fine when the intent is obvious
Func<int, bool> isEven = n => n % 2 == 0;

// Named delegate when the type name itself communicates purpose
delegate bool Predicate<T>(T item);
```

Operator overloading is appropriate when types represent composable domain concepts and the operators have obvious mathematical or domain meaning (e.g., `Vector3` arithmetic, combining `Expression` trees).

## Fluent API Chaining

When building up configuration or composing behavior, prefer fluent method chaining. Extension methods are well-suited for building fluent APIs without modifying the original types.

The chain should read as a sequence of refinements — start broad, narrow down. Like how LINQ reads:

```csharp
var topProducts = products
    .Where(p => p.Rating > 4.0)
    .OrderByDescending(p => p.Sales)
    .Take(10);
```

Or how middleware pipelines chain in ASP.NET Core:

```csharp
app.UseAuthentication()
   .UseAuthorization()
   .UseRateLimiting();
```

Keep each chain method focused on one concern.

**Break long chains into named intermediates.** When a fluent chain spans many lines or has logically distinct phases, introduce a named variable at a natural boundary. The variable name documents what that intermediate result represents, making the pipeline easier to read and debug:

```csharp
// Good — named intermediates at logical boundaries
var ordersByCustomer = orders
    .Where(o => o.Date >= cutoff)
    .ToLookup(o => o.CustomerId);

var reports = customers
    .Select(c => (Customer: c, Orders: ordersByCustomer[c.Id].ToList()))
    .Where(x => x.Orders.Count > 0)
    .Select(x => BuildReport(x.Customer, x.Orders))
    .ToList();
```

**Keep lambda bodies simple.** If a lambda grows beyond a couple of lines or contains its own local variables, extract it into a named method. The method name communicates intent better than an inline block.

## Tuple Returns

Return tuples from factory methods when the grouped values are naturally understood together and the names make the meaning clear at the call site:

```csharp
var (min, max) = FindRange(values);
var (user, token) = await AuthenticateAsync(credentials);
```

Avoid tuples when the grouping is non-obvious or the names would be ambiguous — use a record or dedicated type instead.

## Immutability and Statelessness

Favor immutable data and stateless functions for readability and testability. No hidden state means no surprise side effects.

- Prefer pure functions that take inputs and return outputs over methods that mutate state
- Use `with` expressions for producing modified copies of records
- Use `IEnumerable` with `yield return` for lazy sequences rather than building mutable collections

```csharp
// Immutable update — like how System.Collections.Immutable works
var updated = original with { Timeout = TimeSpan.FromSeconds(30) };

// Lazy evaluation — like LINQ's deferred execution
IEnumerable<T> Where<T>(this IEnumerable<T> source, Func<T, bool> predicate)
{
    foreach (var item in source)
        if (predicate(item))
            yield return item;
}
```

**Pragmatic exception:** When immutability introduces observable performance overhead (excessive allocations in a hot path, large struct copies), use mutable state with clear scoping. The goal is readability and testability, not dogma.

## Use `var` Generously

Default to `var` when the type is clear from the right-hand side — whether it's a constructor, method call, LINQ result, or destructured tuple. Explicit types are fine when they're short and genuinely add clarity, but don't spell out `decimal` or `string` when the context already makes it obvious.

```csharp
var lookup = new Dictionary<string, List<(int Id, string Name)>>();
var discount = CalculateDiscount(subtotal, customer);
var (host, port) = ParseEndpoint(connectionString);
```

## Method Size and Decomposition

Keep methods focused — rarely exceeding ~30 lines. When a method grows, decompose into smaller composable pieces with clear single purposes.

Prefer static methods when the logic doesn't depend on instance state.

## Expression-Oriented Style

- **Switch expressions** over switch statements for mapping/branching
- **LINQ chains** for transforms and filtering over manual loops
- **Expression-bodied members** for simple one-liners

```csharp
string label = severity switch
{
    Severity.Error => "Error",
    Severity.Warning => "Warning",
    _ => "Info"
};
```

**Avoid chained ternaries across multiple lines.** A single-line ternary is fine when short (`var x = cond ? a : b;`). But chaining ternaries vertically harms readability — use a switch expression instead:

```csharp
// Bad — chained ternary is hard to scan
decimal discount =
    customer.IsPremium ? subtotal * 0.1m
    : subtotal > 100   ? subtotal * 0.05m
    :                     0m;

// Good — switch expression reads as a clear decision table
decimal discount = customer switch
{
    { IsPremium: true } => subtotal * 0.1m,
    _ when subtotal > 100 => subtotal * 0.05m,
    _ => 0m
};
```

**Avoid null-sentinel patterns in LINQ pipelines.** Don't use `Select` returning null followed by `.Where(x => x is not null)`. Instead, filter first, then project — or use an anonymous type to carry intermediate state through the pipeline:

```csharp
// Bad — null as flow control
items.Select(x => HasData(x) ? Transform(x) : null)
     .Where(x => x is not null)

// Good — filter then project
items.Where(x => HasData(x))
     .Select(x => Transform(x))
```

## Completeness

When writing or refactoring code, include all type definitions needed for the code to compile — records, classes, enums referenced by the output. Don't leave types undefined unless they are obviously from an external library.

## Comments

Use comments for non-obvious logic — algorithm choices, magic constants, domain-specific rationale. XML doc comments are appropriate on public API methods to describe purpose and contracts. Don't add comments that merely restate what the code already says through its naming and structure.
