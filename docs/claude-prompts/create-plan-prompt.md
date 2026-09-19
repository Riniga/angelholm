# How to create a Plan

## Prompt

Create all implementation plans for MVP:  `docs/mvp/004-multimodal-city.md`

Requirements:

- Create a COMPLETE but stepwise plan for curser to be able to execute the implementation
- Break everything into small, concrete TODOs
- Group todos in Phases with a name used for the commit of this phase

Output format:

1. Goal
2. Assumptions
3. Proposed file changes
4. Step-by-step TODO grouped into phases
5. Risks / open questions

Save the plan in the folder: `docs/plans/004-multimodal-city.plan.md`

---

## Step by step
1. Create a well structured MVP doucment (use the template) out of the current roadmap from the documentation
2. Run the prompts above
3. Verify and Adjust the plan
5. Create proper branch for the mvp
6. Exceute the plan step by step.
7. Commit continously
8. End with proper refactoring, validation: prompts:
     - Perform a code review with focus on clean code and understnablility. Make sure we comply with setup/guidelines/standards.md
     - Perform a final review of all documentation, readme files and others, make sure evverything is upp to date and well documented
9. When completely done close branch with pull-request

# Create an Implementation Plan

## Prompt

Create an implementation plan for:

```text
docs/mvp/<nn>-<description>.md
```

Before creating the plan, read:

* `docs/development/development-process.md`
* `docs/architecture/overview.md`
* `docs/standards/coding.md`
* `docs/standards/testing.md`
* `docs/standards/git.md`

### Requirements

* Create a complete but simple implementation plan.
* Break the work into small TODOs.
* Group TODOs into logical phases.
* Suggest a commit message for each phase.
* Keep each TODO small enough to implement and verify independently.
* Identify files likely to change.
* Do **not** write implementation code.

### Output

Save the plan as:

```text
docs/plans/<nn>-<description>.plan.md
```

Use this structure:

1. Goal
2. Assumptions
3. Proposed file changes
4. Implementation phases with TODOs
5. Risks / Open questions

---

# Workflow

1. Create or select an MVP.
2. Create the implementation plan.
3. Review and adjust the plan.
4. Create a feature branch.
5. Implement one phase at a time.
6. Commit after each completed phase.
7. Run tests and update documentation.
8. Create a Pull Request.
