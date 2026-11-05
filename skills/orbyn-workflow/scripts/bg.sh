#!/bin/sh
# Run a long command in the background and wait for it in one blocking call. POSIX sh (bash, dash, zsh), macOS and Linux.
#
#   bg.sh [--root DIR] start [--name N] [--cwd D] [--on-done CMD] -- <command...>
#   bg.sh [--root DIR] wait <id> [--max S] [--tail N]
#   bg.sh [--root DIR] status <id> [--tail N]
#
# `start` returns at once with {id, root, log, wait}. `wait` blocks inside this script until the job exits, its
# supervisor dies or --max seconds pass, then prints {id, state, exit_code, elapsed_seconds, log, tail} and exits with the
# job's code (3 while running, 4 when lost). Same interface as bg.py; no Python needed.
# Jobs live under $ORBYN_BG_ROOT or a per-user temp folder.

RUNNING=3
LOST=4

# --- small helpers ---------------------------------------------------------------------------------------------

die() {
  printf 'bg: %s\n' "$1" >&2
  exit "${2:-1}"
}

now() { date +%s; }

# JSON string body of stdin: escapes backslash, quote and control characters; joins lines with \n (no trailing one).
json_body() {
  LC_ALL=C awk '
    function rep(s, from, to,   out, p) {
      out = ""
      while ((p = index(s, from)) > 0) { out = out substr(s, 1, p - 1) to; s = substr(s, p + length(from)) }
      return out s
    }
    BEGIN {
      ORS = ""; bs = sprintf("%c", 92)
      for (i = 1; i < 32; i++) if (i != 9 && i != 13) ctl[i] = sprintf("%c", i)
    }
    {
      line = rep($0, bs, bs bs)
      line = rep(line, "\"", bs "\"")
      line = rep(line, sprintf("%c", 9), bs "t")
      line = rep(line, sprintf("%c", 13), bs "r")
      for (i = 1; i < 32; i++) if (i in ctl && index(line, ctl[i]) > 0) line = rep(line, ctl[i], bs sprintf("u%04x", i))
      if (NR > 1) printf "%s", bs "n"
      print line
    }'
}

# "..." JSON string of the argument. Plain text needs no process; anything with a backslash, quote or control
# character goes through awk.
jstr() {
  case $1 in
    *\\* | *\"* | *[[:cntrl:]]*)
      printf '"'
      printf '%s\n' "$1" | json_body
      printf '"'
      ;;
    *) printf '"%s"' "$1" ;;
  esac
}

# Write the text atomically: temp file, then rename.
atomic_write() {
  printf '%s\n' "$2" >"$1.tmp" && mv -f "$1.tmp" "$1"
}

# Sets NUMBER to a number field out of a one-line JSON file this script wrote (empty when absent). No processes.
json_number() {
  NUMBER=
  _line=
  IFS= read -r _line <"$1" 2>/dev/null || true
  _key="\"$2\":"
  _rest=${_line#*"$_key"}
  [ "$_rest" != "$_line" ] || return 0
  _rest=${_rest# }
  NUMBER=${_rest%%[!0-9]*}
}

default_root() {
  if [ -n "${ORBYN_BG_ROOT:-}" ]; then
    printf '%s' "$ORBYN_BG_ROOT"
  else
    printf '%s/orbyn-bg-%s' "$(printf '%s' "${TMPDIR:-/tmp}" | sed 's|/*$||')" "${USER:-${LOGNAME:-user}}"
  fi
}

is_pid_alive() {
  [ -n "$1" ] && kill -0 "$1" 2>/dev/null
}

# Sets JOBDIR or dies. Refuses ids with a slash, a backslash or a leading dot, and unknown ids.
job_dir() {
  case "$1" in
    '' | */* | *\\* | .*) die "no job '$1' under $ROOT" ;;
  esac
  [ -f "$ROOT/$1/job.json" ] || die "no job '$1' under $ROOT"
  JOBDIR=$ROOT/$1
}

read_exit() {
  json_number "$JOBDIR/exit.json" exit_code
  EXIT_CODE=$NUMBER
  json_number "$JOBDIR/exit.json" ended
  ENDED=$NUMBER
}

# Sets STATE, EXIT_CODE, ENDED, CREATED for the job in $JOBDIR: done, running, lost or starting.
job_state() {
  json_number "$JOBDIR/job.json" created
  CREATED=${NUMBER:-0}
  EXIT_CODE=
  ENDED=
  if [ -f "$JOBDIR/exit.json" ]; then
    STATE=done
    read_exit
    return 0
  fi
  if [ ! -f "$JOBDIR/supervisor.json" ]; then
    if [ $(($(now) - CREATED)) -lt 30 ]; then STATE=starting; else STATE=lost; fi
    return 0
  fi
  json_number "$JOBDIR/supervisor.json" pid
  if is_pid_alive "$NUMBER"; then
    STATE=running
  elif [ -f "$JOBDIR/exit.json" ]; then # finished between the two reads
    STATE=done
    read_exit
  else
    STATE=lost
  fi
}

# Prints the JSON report for the current state and returns the exit code to use.
report() {
  _lines=$1
  _end=${ENDED:-$(now)}
  _elapsed=$((_end - CREATED))
  [ "$_elapsed" -ge 0 ] || _elapsed=0
  _tail=
  if [ "$_lines" -gt 0 ] && [ -f "$JOBDIR/output.log" ]; then
    _tail=$(tail -n "$_lines" "$JOBDIR/output.log" | { iconv -c -f UTF-8 -t UTF-8 2>/dev/null || cat; })
  fi
  if [ "$STATE" = done ]; then _code=${EXIT_CODE:-1}; else _code=null; fi
  {
    printf '{\n  "id": '
    jstr "${JOBDIR##*/}"
    printf ',\n  "state": "%s",\n  "exit_code": %s,\n  "elapsed_seconds": %s,\n  "log": ' "$STATE" "$_code" "$_elapsed"
    jstr "$JOBDIR/output.log"
    printf ',\n  "tail": '
    jstr "$_tail"
    printf '\n}\n'
  }
  case $STATE in
    done)
      if [ "$_code" -ge 0 ] 2>/dev/null && [ "$_code" -lt 256 ]; then return "$_code"; fi
      return 1
      ;;
    lost) return $LOST ;;
  esac
  return $RUNNING
}

# --- commands ---------------------------------------------------------------------------------------------------

cmd_start() {
  NAME= CWD= ON_DONE=
  while [ $# -gt 0 ]; do
    case $1 in
      --name) [ $# -ge 2 ] || die "--name needs a value"; NAME=$2; shift 2 ;;
      --cwd) [ $# -ge 2 ] || die "--cwd needs a value"; CWD=$2; shift 2 ;;
      --on-done) [ $# -ge 2 ] || die "--on-done needs a value"; ON_DONE=$2; shift 2 ;;
      --) shift; break ;;
      -*) die "unknown option $1 for start" ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || die "give the command after --"

  umask 077
  mkdir -p "$ROOT" || die "cannot create $ROOT"
  _rand=$(od -An -N3 -tx1 /dev/urandom 2>/dev/null | tr -d ' \n')
  _rand=${_rand:-$$}
  _clock=$(date '+%Y%m%d-%H%M%S %s')
  _created=${_clock#* }
  _id=${_clock% *}-$_rand
  if [ -n "$NAME" ]; then
    _suffix=$(printf '%s' "$NAME" | tr -c 'A-Za-z0-9_-' '-')
    _id=$_id-$(printf '%.40s' "$_suffix")
  fi
  JOBDIR=$ROOT/$_id
  mkdir "$JOBDIR" || die "cannot create $JOBDIR"
  if [ -n "$CWD" ]; then _cwd=$(cd "$CWD" 2>/dev/null && pwd -P) || _cwd=$CWD; else _cwd=$(pwd -P); fi

  _json='{"id": '$(jstr "$_id")', "command": ['
  _sep=
  for _arg in "$@"; do
    _json=$_json$_sep$(jstr "$_arg")
    _sep=', '
  done
  _json=$_json'], "cwd": '$(jstr "$_cwd")', "on_done": '
  if [ -n "$ON_DONE" ]; then _json=$_json$(jstr "$ON_DONE"); else _json=${_json}null; fi
  atomic_write "$JOBDIR/job.json" "$_json, \"created\": $_created}"

  : >"$JOBDIR/output.log"
  if command -v setsid >/dev/null 2>&1; then
    setsid nohup sh "$SELF" _supervise "$JOBDIR" "$ON_DONE" "$_cwd" -- "$@" </dev/null >/dev/null 2>&1 &
  else
    nohup sh "$SELF" _supervise "$JOBDIR" "$ON_DONE" "$_cwd" -- "$@" </dev/null >/dev/null 2>&1 &
  fi

  printf '{\n  "id": '
  jstr "$_id"
  printf ',\n  "root": '
  jstr "$ROOT"
  printf ',\n  "log": '
  jstr "$JOBDIR/output.log"
  printf ',\n  "wait": '
  jstr "bg.sh wait $_id"
  printf '\n}\n'
}

# Runs detached: start the command, record its exit code, then run the optional on-done command.
cmd_supervise() {
  _dir=$1 _on_done=$2 _cwd=$3
  shift 4 # path, on-done, cwd, --
  _log=$_dir/output.log
  _id=${_dir##*/}
  if ! cd "$_cwd" 2>/dev/null; then
    _err="could not start: cannot enter $_cwd"
    printf 'bg: %s\n' "$_err" >>"$_log"
    atomic_write "$_dir/exit.json" "{\"exit_code\": 127, \"ended\": $(now), \"error\": $(jstr "$_err")}"
    return 0
  fi
  "$@" </dev/null >>"$_log" 2>&1 &
  _child=$!
  atomic_write "$_dir/supervisor.json" "{\"pid\": $$, \"child_pid\": $_child, \"started\": $(now)}"
  wait "$_child"
  _code=$?
  atomic_write "$_dir/exit.json" "{\"exit_code\": $_code, \"ended\": $(now)}"
  if [ -n "$_on_done" ]; then
    BG_JOB_ID=$_id BG_EXIT_CODE=$_code BG_LOG=$_log sh -c "$_on_done" </dev/null >>"$_dir/on_done.log" 2>&1
  fi
  return 0
}

cmd_wait() {
  [ $# -gt 0 ] || die "wait needs a job id"
  _job=$1
  shift
  _max=540 _lines=40
  while [ $# -gt 0 ]; do
    case $1 in
      --max) [ $# -ge 2 ] || die "--max needs a value"; _max=${2%%.*}; shift 2 ;;
      --tail) [ $# -ge 2 ] || die "--tail needs a value"; _lines=$2; shift 2 ;;
      *) die "unknown option $1 for wait" ;;
    esac
  done
  case ${_max:-0} in *[!0-9]*) die "--max must be a number of seconds" ;; esac
  case $_lines in '' | *[!0-9]*) die "--tail must be a number" ;; esac
  job_dir "$_job"
  _deadline=$(($(now) + ${_max:-0}))
  while :; do
    job_state
    if [ "$STATE" = done ] || [ "$STATE" = lost ] || [ "$(now)" -ge "$_deadline" ]; then
      report "$_lines"
      exit $?
    fi
    sleep 0.2 2>/dev/null || sleep 1
  done
}

cmd_status() {
  [ $# -gt 0 ] || die "status needs a job id"
  _job=$1
  shift
  _lines=40
  while [ $# -gt 0 ]; do
    case $1 in
      --tail) [ $# -ge 2 ] || die "--tail needs a value"; _lines=$2; shift 2 ;;
      *) die "unknown option $1 for status" ;;
    esac
  done
  case $_lines in '' | *[!0-9]*) die "--tail must be a number" ;; esac
  job_dir "$_job"
  job_state
  report "$_lines"
  exit $?
}

# --- main ------------------------------------------------------------------------------------------------------

case $0 in
  /*) SELF=$0 ;;
  *) SELF=$(pwd -P)/$0 ;;
esac
ROOT=$(default_root)

if [ "${1:-}" = --root ]; then
  [ $# -ge 2 ] || die "--root needs a value"
  ROOT=$2
  shift 2
fi

[ $# -gt 0 ] || die "usage: bg.sh [--root DIR] start|wait|status ..." 2
ACTION=$1
shift
case $ACTION in
  start) cmd_start "$@" ;;
  wait) cmd_wait "$@" ;;
  status) cmd_status "$@" ;;
  _supervise) cmd_supervise "$@" ;;
  *) die "unknown action '$ACTION' (use start, wait or status)" 2 ;;
esac
