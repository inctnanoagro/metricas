#!/usr/bin/env zsh

testar() {
  local script_dir
  script_dir="$(cd "$(dirname "${(%):-%N}")" && pwd)"
  "${script_dir}/../testar.sh" "$@"
}
