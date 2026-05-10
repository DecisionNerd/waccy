## Linked Issue

Closes #

## Outcome

- [ ] The user-visible outcome is described in the linked issue.
- [ ] BDD feature expectations were added or updated when behavior changed.
- [ ] Unit or integration coverage was added for implementation details.

## Checks

- [ ] `uv run ruff check`
- [ ] `uv run mypy src/waccy`
- [ ] `uv run pytest --cov=src/waccy --cov-report=term-missing --cov-report=xml --cov-fail-under=80`
