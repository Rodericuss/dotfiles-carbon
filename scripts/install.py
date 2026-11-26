#!/usr/bin/env python3
"""Explicit local theme deployment with a persistent per-file rollback manifest.

Migrates from the earlier Mainframe Latão / Neobrutal overlays: their integration blocks are
replaced and their late-loading files are neutralized (all backed up first)."""
import argparse,datetime,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');p.add_argument('--restore',action='store_true');p.add_argument('--home',type=Path,default=Path.home());a=p.parse_args()
home=a.home;state=home/'.local/state/carbon';manifest_path=state/'restore.json'
manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
backup=state/'backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
OLD=('NEOBRUTAL','MAINFRAME','CARBON')

def write(target,data,mode=0o644):
 if a.dry_run:print('WRITE',target);return
 if str(target) not in manifest:
  if target.exists() or target.is_symlink():
   saved=backup/str(len(manifest));saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved,follow_symlinks=False);manifest[str(target)]=str(saved)
  else:manifest[str(target)]=None
  state.mkdir(parents=True,exist_ok=True);temp=manifest_path.with_suffix('.tmp');temp.write_text(json.dumps(manifest,indent=2));temp.replace(manifest_path)
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.is_symlink():target.unlink()
 tmp=target.with_name(target.name+'.carbon-tmp');tmp.write_bytes(data);tmp.chmod(mode);tmp.replace(target)
 print('OK',target)
def strip_blocks(old,kind):
 for theme in OLD:old=re.sub(r'/\* BEGIN '+theme+' '+kind+r' \*/.*?/\* END '+theme+' '+kind+r' \*/\n?','',old,flags=re.S)
 return old
def block(old,name,text):
 return old.rstrip()+('\n' if old.strip() else '')+f'/* BEGIN CARBON {name} */\n'+text.rstrip()+f'\n/* END CARBON {name} */\n'
def read(p):return p.read_text() if p.exists() else ''

if a.restore:
 for name,saved in reversed(list(manifest.items())):
  target=Path(name)
  if a.dry_run:print('RESTORE',target);continue
  if saved:
   if target.is_symlink():target.unlink()
   shutil.copy2(saved,target,follow_symlinks=False)
  else:target.unlink(missing_ok=True)
 if not a.dry_run and manifest_path.exists():manifest_path.rename(state/('restored-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.json'))
 sys.exit(0)

for src in sorted((ROOT/'config').rglob('*')):
 if not src.is_file() or '__pycache__' in src.parts:continue
 if src.relative_to(ROOT/'config').as_posix() in ('hypr/hyprland.lua','kitty/kitty.conf'):continue
 data=src.read_bytes()
 if src.name=='hyprpaper.conf':data=('splash = false\nwallpaper {\n    monitor =\n    path = '+str(home/'.config/carbon/wallpaper.png')+'\n}\n').encode()
 write(home/'.config'/src.relative_to(ROOT/'config'),data,0o755 if src.stat().st_mode&0o111 else 0o644)
for src in sorted((ROOT/'fonts').glob('*')):write(home/'.local/share/fonts/carbon'/src.name,src.read_bytes())

# Earlier themes load after ours (alphabetical conf.d, extra lazy.nvim spec): neutralize them.
for rel,stub in [('fish/conf.d/zz-mainframe.fish','# Superseded by zz-carbon.fish (Carbon theme).\n'),
                 ('fontconfig/conf.d/90-mainframe.conf','<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<!-- Superseded by 90-carbon.conf -->\n<fontconfig/>\n'),
                 ('nvim/lua/custom/plugins/neobrutalist.lua','-- Superseded by carbon.lua (Carbon theme).\nreturn {}\n')]:
 if (home/'.config'/rel).exists():write(home/'.config'/rel,stub.encode())

# Kitty: keep keymaps, shell integration and local settings; swap the theme include.
kitty=home/'.config/kitty/kitty.conf';old=read(kitty)
for line in ('# Mainframe Latão theme overlay\n','# Carbon theme overlay\n'):old=old.replace(line,'')
old=re.sub(r'^include (?:neobrutal|mainframe|carbon)\.conf\s*$','',old,flags=re.M)
write(kitty,(old.rstrip()+'\n\n# Carbon theme overlay\ninclude carbon.conf\n').encode())

# Hyprland: add the Lua theme last, keeping hardware/input/workspace configuration intact.
hypr=home/'.config/hypr/hyprland.lua';old=read(hypr)
if old:
 if '-- Mainframe Latão: the final visual settings' in old:old=old[:old.index('-- Mainframe Latão: the final visual settings')]
 old=re.sub(r'-- BEGIN (?:MAINFRAME|CARBON) INTEGRATION.*?-- END (?:MAINFRAME|CARBON) INTEGRATION\n?','',old,flags=re.S)
 # These shortcuts are supplied by the theme, not registered twice.
 keys=['"SUPER + TAB"','"SUPER + T"','"SUPER + N"','"SUPER + ALT + F"','"F8"','"XF86MonBrightnessUp"','"XF86MonBrightnessDown"','"XF86AudioRaiseVolume"','"XF86AudioLowerVolume"','"XF86AudioMute"','"XF86AudioMicMute"','"F7"','"SUPER + SPACE"','"SUPER + O"','mainMod .. " + SPACE"','mainMod .. " + O"']
 old='\n'.join(line for line in old.splitlines() if not (line.strip().startswith('hl.bind(') and any(x in line for x in keys)))
 old='\n'.join(line for line in old.splitlines() if not re.search(r'hl\.exec_cmd\("~/\.config/(?:neobrutal|mainframe|carbon)/control start"\)',line))
 old=old.rstrip()+'\n-- BEGIN CARBON INTEGRATION\ndofile(os.getenv("HOME") .. "/.config/hypr/carbon.lua")\n-- END CARBON INTEGRATION\n'
 write(hypr,old.encode())
else:print('Hyprland: no existing Lua config; source ~/.config/hypr/carbon.lua manually.')
# F7 normal/focus pair: swap the theme's integration block in place, keeping any override after it.
CARBON_BLOCK='-- BEGIN CARBON INTEGRATION\ndofile(os.getenv("HOME") .. "/.config/hypr/carbon.lua")\n-- END CARBON INTEGRATION\n'
for name in ('hypr_config1.lua','hypr_config2.lua'):
 pair=home/'.config/hypr'/name;old=read(pair)
 if 'MAINFRAME INTEGRATION' in old:write(pair,re.sub(r'-- BEGIN MAINFRAME INTEGRATION.*?-- END MAINFRAME INTEGRATION\n?',lambda m:CARBON_BLOCK,old,flags=re.S).encode())

# Compatibility entry points for existing startup commands and launchers.
write(home/'.config/neobrutal/control',b'#!/usr/bin/env bash\nexec "$HOME/.config/carbon/control" "$@"\n',0o755)
write(home/'.config/mainframe/control',b'#!/usr/bin/env bash\nexec "$HOME/.config/carbon/control" "$@"\n',0o755)
write(home/'scripts/f1_hypr_conf.sh',b'#!/usr/bin/env bash\nexec "$HOME/.config/carbon/control" focus\n',0o755)

# Firefox: match installed profiles, including profile groups absent in profiles.ini.
for profile in sorted(p for root in ('.mozilla/firefox','.config/mozilla/firefox','snap/firefox/common/.mozilla/firefox') for p in (home/root).glob('*')):
 prefs=profile/'prefs.js'
 if not profile.is_dir() or not prefs.exists():continue
 uuid=None
 for match in re.finditer(r'user_pref\("extensions.webextensions.uuids",\s*("(?:\\.|[^"\\])*")\s*\);',read(prefs)):
  try:uuid=json.loads(json.loads(match.group(1))).get('{3c078156-979c-498b-8990-85f7987dd929}')
  except (ValueError,AttributeError):pass
 css=(ROOT/'config/firefox/userChrome.css').read_text()
 if not uuid:css=css.replace('#TabsToolbar { display:none !important; }','').replace('#sidebar-header { display:none !important; }','')
 chrome=profile/'chrome/userChrome.css';old=strip_blocks(read(chrome),'FIREFOX')
 if old.startswith('/* Neobrutal browser chrome.'):old=''
 write(chrome,block(old,'FIREFOX',css).encode())
 content=profile/'chrome/userContent.css';old=strip_blocks(strip_blocks(read(content),'SIDEBERY'),'CONTENT')
 css='@-moz-document url("about:blank"),url("about:newtab"),url("about:home") { html,body { background:#161616 !important; color:#f2f4f8 !important; } }\n'
 if uuid and re.fullmatch('[a-fA-F0-9-]{36}',uuid):css+='@-moz-document url-prefix("moz-extension://'+uuid+'/") {\n'+(ROOT/'config/firefox/sidebery.css').read_text()+'\n}\n'
 write(content,block(old,'CONTENT',css).encode())
 user=profile/'user.js';settings='user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\nuser_pref("sidebar.position_start", true);\nuser_pref("sidebar.revamp", false);\nuser_pref("browser.startup.page", 3);\nuser_pref("browser.startup.homepage", '+json.dumps((home/'.config/carbon/home.html').as_uri())+');\n'
 write(user,block(strip_blocks(read(user),'PREFERENCES'),'PREFERENCES',settings).encode())
print('Manifest:',manifest_path)
