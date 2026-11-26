#!/usr/bin/env bash
set -euo pipefail
control="$HOME/.config/carbon/control"
[[ -x "$control" ]] || { echo 'Run ./apply.sh first.' >&2; exit 1; }
mkdir -p "$HOME/.local/state/carbon"
fc-cache -f "$HOME/.local/share/fonts/carbon"
command -v bat >/dev/null && bat cache --build >/dev/null
# Stop the Mainframe Latão panel if it is still running (it holds port 47831 and its own socket).
pkill -f "$HOME/.config/mainframe/shell.py" || true
"$control" stop
pkill -x waybar || true
"$control" start
hyprctl reload
# Restart, not reload: a reload keeps the config path chosen at startup, so a
# daemon started before ~/.config/swaync/config.json existed keeps the defaults.
if systemctl --user is-active -q swaync.service; then
  systemctl --user restart swaync.service
else
  pkill -x swaync || true
  nohup swaync > "$HOME/.local/state/carbon/swaync.log" 2>&1 < /dev/null &
fi
if command -v hyprpaper >/dev/null; then
  pkill -x hyprpaper || true
  nohup hyprpaper > "$HOME/.local/state/carbon/hyprpaper.log" 2>&1 < /dev/null &
fi
printf 'Carbon is active. Reopen terminal apps; restart Firefox to load its chrome CSS.\n'
