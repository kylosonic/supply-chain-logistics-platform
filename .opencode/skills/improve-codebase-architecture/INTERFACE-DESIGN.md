# Interface Design

When drafting the blueprint for a deepening candidate, define the interface following these constraints before detailing the execution steps.

Uses the vocabulary in [LANGUAGE.md](LANGUAGE.md) - **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Define the problem space for the chosen candidate in the blueprint:

- The constraints the new interface satisfies.
- The dependencies it relies on, and which category they fall into (see [DEEPENING.md](DEEPENING.md)).

### 2. Design the Interface

Draft the interface optimizing for depth and locality. Ensure the design satisfies the following requirements:

- Minimize the interface. Aim for the fewest entry points necessary, maximizing leverage per entry point.
- Optimise for the most common caller. Make the default case trivial.
- Design around ports & adapters for cross-seam dependencies.

Include both [LANGUAGE.md](LANGUAGE.md) vocabulary and `CONTEXT.md` vocabulary in the specification so all naming is consistent with the architecture language and the project's domain language.

### 3. Blueprint Output Requirements

The interface section of the blueprint must output:

1. Interface specification (types, methods, params, invariants, ordering, error modes).
2. A usage example showing how callers will use it.
3. What the implementation hides behind the seam.
4. Dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md)).
