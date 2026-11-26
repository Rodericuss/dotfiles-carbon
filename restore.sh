#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == '--dry-run' ]]; then
  exec python3 scripts/install.py --restore --dry-run
fi
if [[ -x "$HOME/.config/carbon/control" ]]; then
  if [[ "$("$HOME/.config/carbon/control" focus-status)" == true ]]; then
    "$HOME/.config/carbon/control" focus
  fi
  "$HOME/.config/carbon/control" stop
fi
systemctl --user stop swaync.service || true
pkill -x swaync || true
pkill -x waybar || true
python3 scripts/install.py --restore
python3 - <<'PY'
import json,subprocess
from pathlib import Path
p=Path.home()/'.local/state/carbon/services.json'
if p.exists():
    state=json.loads(p.read_text())
    if state.get('is-active')=='active':
        subprocess.run(['systemctl','--user','start','mako.service'])
    p.rename(p.with_name('services-restored.json'))
PY
hyprctl reload
nohup waybar > "${XDG_RUNTIME_DIR:-/tmp}/carbon-restored-waybar.log" 2>&1 < /dev/null &
printf 'Configuration files restored. Restart your desktop session and browser. See docs/INSTALL.md for Firefox preference and add-on rollback.\n'
