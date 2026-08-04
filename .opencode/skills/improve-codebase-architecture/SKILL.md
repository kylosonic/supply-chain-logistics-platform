---
name: improve-codebase-architecture
description: Find deepening opportunities in a codebase and write an execution blueprint for the build agent. Informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when orchestrating a refactor to consolidate tightly-coupled modules or make a codebase more testable and AI-navigable.
---

# Improve Codebase Architecture

Surface architectural friction and draft an immutable execution blueprint for **deepening opportunities** - refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability.

## Glossary

Use these terms exactly in every blueprint. Consistent language is the point - do not drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](LANGUAGE.md).

- **Module** - anything with an interface and an implementation (function, class, package, slice).
- **Interface** - everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** - the code inside.
- **Depth** - leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** - where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary.")
- **Adapter** - a concrete thing satisfying an interface at a seam.
- **Leverage** - what callers get from depth.
- **Locality** - what maintainers get from depth: change, bugs, knowledge concentrated in one place.

Key principles (see [LANGUAGE.md](LANGUAGE.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is strictly a consumer of the project's architecture documents. The domain language gives names to good seams; ADRs record decisions the skill must not violate.

## Process

### 1. The Graphify Mandate (Exploration)

Read the project's domain glossary and any ADRs in the area you are touching first.

You MUST use the terminal to execute `graphify query` and `graphify explain` on the target files before drafting. Map the Abstract Syntax Tree (AST). Do not rely on raw text reading. Note where you experience structural friction:

- Which files are overgrown nodes with too many edges (e.g., monolithic entry points)?
- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** - interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how they are called (no **locality**)?

Apply the **deletion test** to anything you suspect is shallow.

### 2. Interface Design

Once a target is identified, design the new interface using the constraints in [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md). The interface must be finalized conceptually before writing the execution steps.

### 3. Strict Import Mapping (CRITICAL)

Before finalizing the blueprint, you MUST mentally index all existing fields, variables, type hints, and imports in the original files. 

- You must not remove unused fields or imports unless explicitly instructed to clean up or optimize. 
- Existing schemas and data structures must be preserved in full. For legacy support, if a file originally contained 20 fields, the updated modular version must retain all 20 fields.
- Every function call and type hint in the newly separated files MUST have a corresponding, correct import. 
- Prefer absolute imports, or use explicit relative imports only when strictly safe.

### 4. Blueprint Generation

Do NOT ask the user questions. Output a highly structured, immutable execution blueprint for the `@build` agent. The blueprint must include:

1. **Architecture Context**: The files involved, the friction being solved, and the target dependency categories (see [DEEPENING.md](DEEPENING.md)).
2. **The New Interface**: Types, methods, parameters, and invariants.
3. **Strict Import Map**: Explicit lists of all functions, type hints, and variables being moved, along with the exact absolute import statements required for the new files to compile seamlessly.
4. **Execution Steps**: Step-by-step instructions for the `@build` agent to execute the refactor, including exact file paths and test coverage requirements.
