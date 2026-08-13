lint:
	uvx ruff check

.PHONY: test
test:
	uvx pytest

invite.png: invite-flow.dot
	dot -T png $< -o$@
