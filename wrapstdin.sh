#!/usr/bin/env bash
# run commands as if they accept stdin.
#
# Usage:
#   echo "test" | ./wrapstdin.sh [-d] <command> [args...]
#
# -d : create a temp *directory* under /tmp, write stdin to a file inside it,
#      and pass the directory (not the file) to the wrapped command.
#
set -euo pipefail

use_dir=false
if [ "${1:-}" = "-d" ]; then
    use_dir=true
    shift
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 [-d] <command> [args...]" >&2
    exit 1
fi

tmpfile=""
tmpdir=""

cleanup() {
    if $use_dir; then
        [ -n "$tmpdir" ] && rm -rf -- "$tmpdir"
    else
        [ -n "$tmpfile" ] && rm -f -- "$tmpfile"
    fi
}
trap cleanup EXIT INT TERM

if $use_dir; then
    tmpdir="$(mktemp -d /tmp/wrapstdin.XXXXXX)"
    tmpfile="$tmpdir/stdin.py"
    cat >"$tmpfile"
    "$@" "$tmpdir"
else
    tmpfile="$(mktemp /tmp/wrapstdin.XXXXXX.py)"
    cat >"$tmpfile"
    "$@" "$tmpfile"
fi

