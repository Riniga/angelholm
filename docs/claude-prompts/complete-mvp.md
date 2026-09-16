# Complete an MVP

Use this prompt when all implementation phases for an MVP are completed and the work should be prepared for Pull Request.

## Prompt

    Complete the MVP and prepare it for Pull Request.

    Read:

    * `docs/development/development-process.md`
    * `docs/standards/coding.md`
    * `docs/standards/testing.md`
    * `docs/standards/git.md`
    * `docs/architecture/overview.md`
    * the relevant MVP document in `docs/mvp/`
    * the relevant implementation plan in `docs/plans/`

    Review the full change set.

    Check that:

    * the MVP goal is fulfilled
    * all acceptance criteria are met
    * the implementation plan is completed and updated
    * all relevant tests pass
    * code follows the coding standard
    * the solution is simple and understandable
    * no unnecessary complexity has been introduced
    * no unrelated changes are included
    * documentation is updated
    * architecture documentation is updated if needed
    * ADRs are created for important architectural decisions
    * README files are updated if needed
    * no secrets, temporary files or generated artifacts are committed

    If anything is missing, fix it.

    After fixing, run the relevant validation again.

    When everything is ready, provide:

    1. Summary of completed work
    2. Validation performed
    3. Documentation updated
    4. Remaining risks or open questions
    5. Suggested Pull Request title
    6. Suggested Pull Request description

    Do not merge the Pull Request.
