import json
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class InstallTests(unittest.TestCase):
 def test_reapply_preserves_backup_and_local_hypr_config(self):
  with tempfile.TemporaryDirectory() as folder:
   home=Path(folder);rofi=home/'.config/rofi/config.rasi';rofi.parent.mkdir(parents=True);rofi.write_text('original\n')
   hypr=home/'.config/hypr/hyprland.lua';hypr.parent.mkdir(parents=True);hypr.write_text('-- hardware settings belong to this machine\nhl.monitor({output="TEST",mode="preferred"})\n')
   kitty=home/'.config/kitty/kitty.conf';kitty.parent.mkdir(parents=True);kitty.write_text('map ctrl+x new_window\n')
   def apply(*args):subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--home',folder,*args],check=True,stdout=subprocess.DEVNULL)
   apply('--dry-run');self.assertFalse((home/'.config/carbon').exists())
   apply();apply()
   self.assertEqual(hypr.read_text().count('-- BEGIN CARBON INTEGRATION'),1)
   self.assertIn('output="TEST"',hypr.read_text())
   self.assertIn('map ctrl+x',kitty.read_text());self.assertEqual(kitty.read_text().count('include carbon.conf'),1)
   manifest=json.loads((home/'.local/state/carbon/restore.json').read_text())
   self.assertEqual(Path(manifest[str(rofi)]).read_text(),'original\n')
   self.assertIn(str(home), (home/'.config/hypr/hyprpaper.conf').read_text())
   apply('--restore')
   self.assertEqual(rofi.read_text(),'original\n');self.assertNotIn('CARBON INTEGRATION',hypr.read_text());self.assertFalse((home/'.config/carbon/shell.py').exists())
 def test_migrates_from_mainframe_overlay(self):
  with tempfile.TemporaryDirectory() as folder:
   home=Path(folder)
   hypr=home/'.config/hypr/hyprland.lua';hypr.parent.mkdir(parents=True)
   hypr.write_text('hl.monitor({output="TEST"})\nhl.bind("F8", hl.dsp.exec_cmd("x"))\n-- BEGIN MAINFRAME INTEGRATION\ndofile(os.getenv("HOME") .. "/.config/hypr/mainframe.lua")\n-- END MAINFRAME INTEGRATION\n')
   kitty=home/'.config/kitty/kitty.conf';kitty.parent.mkdir(parents=True);kitty.write_text('map ctrl+x new_window\n\n# Mainframe Latão theme overlay\ninclude mainframe.conf\n')
   pair=home/'.config/hypr/hypr_config2.lua';pair.write_text('-- BEGIN MAINFRAME INTEGRATION\ndofile("mainframe.lua")\n-- END MAINFRAME INTEGRATION\nhl.config({general={gaps_out=0}})\n')
   fish=home/'.config/fish/conf.d/zz-mainframe.fish';fish.parent.mkdir(parents=True);fish.write_text('set -g fish_color_command 9EEA8E\n')
   profile=home/'.mozilla/firefox/abc.default-release';(profile/'chrome').mkdir(parents=True);(profile/'prefs.js').write_text('')
   (profile/'chrome/userChrome.css').write_text('/* mine */\n/* BEGIN MAINFRAME FIREFOX */\nold\n/* END MAINFRAME FIREFOX */\n')
   subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--home',folder],check=True,stdout=subprocess.DEVNULL)
   h=hypr.read_text();self.assertNotIn('MAINFRAME',h);self.assertIn('carbon.lua',h);self.assertIn('output="TEST"',h);self.assertNotIn('"F8"',h)
   k=kitty.read_text();self.assertNotIn('mainframe.conf',k);self.assertIn('include carbon.conf',k);self.assertIn('map ctrl+x',k)
   self.assertNotIn('9EEA8E',fish.read_text())
   self.assertRegex(pair.read_text(),r'carbon\.lua"\)\n-- END CARBON INTEGRATION\nhl\.config')
   chrome=(profile/'chrome/userChrome.css').read_text();self.assertNotIn('MAINFRAME',chrome);self.assertIn('/* mine */',chrome);self.assertEqual(chrome.count('BEGIN CARBON FIREFOX'),1)
   subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--home',folder,'--restore'],check=True,stdout=subprocess.DEVNULL)
   self.assertIn('MAINFRAME INTEGRATION',hypr.read_text());self.assertIn('9EEA8E',fish.read_text())
 def test_themes_firefox_profiles_in_legacy_and_xdg_locations(self):
  with tempfile.TemporaryDirectory() as folder:
   home=Path(folder)
   for root in ('.mozilla/firefox','.config/mozilla/firefox'):
    profile=home/root/'abc.default-release';profile.mkdir(parents=True);(profile/'prefs.js').write_text('')
   subprocess.run(['python3',str(ROOT/'scripts/install.py'),'--home',folder],check=True,stdout=subprocess.DEVNULL)
   for root in ('.mozilla/firefox','.config/mozilla/firefox'):
    self.assertIn('BEGIN CARBON FIREFOX',(home/root/'abc.default-release/chrome/userChrome.css').read_text())
