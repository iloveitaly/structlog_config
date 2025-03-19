setup:
	uv venv && uv sync
	@echo "activate: source ./.venv/bin/activate"

clean:
	rm -rf *.egg-info
	rm -rf .venv

update_copier:
	uv tool run --with jinja2_shell_extension \
		copier@latest update --vcs-ref=HEAD --trust --skip-tasks --skip-answered
