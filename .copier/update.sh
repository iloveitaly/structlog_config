#!/usr/bin/env bash
# Description: this syncs the project with the upstream copier template

uv tool run --with jinja2_shell_extension \
  copier@latest update --vcs-ref=HEAD --trust --skip-tasks --skip-answered
