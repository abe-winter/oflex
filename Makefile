lint:
	uvx ruff check

.PHONY: test
test:
	uv run pytest

invite.png: invite-flow.dot
	dot -T png $< -o$@

pinact:
	pinact run --exclude '^actions\/'
