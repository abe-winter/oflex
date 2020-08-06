lint:
	pylint -E oflex

invite.png: invite-flow.dot
	dot -T png $< -o$@
