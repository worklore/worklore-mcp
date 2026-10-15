#!/usr/bin/env bash
# usage: judge.sh <codex|gemini-pro|gemini-flash|claude-sonnet>
J=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/3bfdd3c9-cfe2-4fd1-a8b7-ce52b613a3aa/scratchpad/mp-eval/judging
mkdir -p $J/raw; W=$(mktemp -d); cd "$W"
case $1 in
  claude-sonnet) env -u WORKLORE_TOKEN timeout 900 claude -p "$(cat $J/judge_prompt.md)" --model sonnet --tools "" \
       --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --setting-sources project,local \
       --settings '{"disableAllHooks":true}' < /dev/null > $J/raw/$1.txt 2> $J/raw/$1.err;;
  *) ~/.local/bin/second-opinion -w $1 -t 900 -f $J/judge_prompt.md > $J/raw/$1.txt 2> $J/raw/$1.err;;
esac
echo "judge $1 rc=$? bytes=$(wc -c < $J/raw/$1.txt)"; rm -rf "$W"
