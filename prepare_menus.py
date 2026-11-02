from pathlib import Path
import shutil
R=Path(__file__).resolve().parent;N='BumpNJump-A1200-StageSelect';O=R.parent/'outputs'/N;O.mkdir(exist_ok=True)
shutil.copyfile(R/'build/BumpNJump-A1200.hdf',O/(N+'.hdf'))
s=(R.parent/'outputs/BumpNJump-A1200-60Hz/BumpNJump-A1200-60Hz.fs-uae').read_text().replace('BumpNJump-A1200-60Hz.hdf',N+'.hdf').replace('hard_drive_0_read_only = 1','hard_drive_0_read_only = 0').replace('60 Hz game clock','Stage Select and Saved Scores').replace('keyboard_key_q = action_joy_1_fire_button\n','');(O/(N+'.fs-uae')).write_text(s)
p=O/'Play-BumpNJump.command';p.write_text('#!/bin/zsh\ncd -- "${0:A:h}"\nexec /Applications/FS-UAE.app/Contents/MacOS/fs-uae ./'+N+'.fs-uae\n');p.chmod(0o755)
(O/'Read-Me.txt').write_text('''BUMP N JUMP — STAGE SELECT, SAVED SCORES AND CONTINUE

Bootable 8 MiB HDF for a stock PAL A1200: 68EC020, AGA, 2 MB Chip RAM,
no expansion RAM or accelerator. Uses your own A1200 Kickstart 3.1 ROM.
No Workbench installation is needed.

NEW MENUS

Start at the original title with Fire or Return. The stage selector opens
before the course loads. Choose any of the 16 original stages with the
joystick or arrows. Left/Up moves back, Right/Down moves forward. Choices
wrap at both ends. Fire or Return starts the selected stage. Release Fire
between choices and confirmation. Each preview uses the original scenery.
All menu letters and numbers use the game's own cartridge font tiles.

Press Tab on the stage selector or title to view the top 10 scores.
Fire, Return or Tab returns from the table.

After game over, qualifying scores prompt for three initials. Use Up/Down
to change a letter, Left/Right to move, and Fire to advance through the
letters. Fire on the third letter saves. You can also type A-Z and press
Return to save. Backspace moves back. The table shows score and stage reached.
Tied scores follow earlier matching scores. Zero scores do not qualify.

After the table, choose YES or NO at Continue. If the score does not
qualify, the Continue prompt opens directly. YES restarts the current stage
with the normal three lives and zero score. The finished run's saved score
stays in the table. NO returns to the original game-over/title sequence.

SAVED SCORES

The HDF must be writable. The supplied profile enables writes.
Scores save immediately after initials entry, inside DH0:HighScores.A and
DH0:HighScores.B. These are small alternating, checksummed saves; the last
valid table is loaded at boot. An interrupted or damaged latest save can
fall back to its predecessor. A failed save stays visible and Fire retries.
Keep a copy of your HDF to back up scores. A fresh HDF starts with an empty
table. Reset only after the SCORES SAVED message appears.

PLAY ON THIS MAC

Unzip and double-click Play-BumpNJump.command. The profile refers to the
Kickstart ROM installed on this Mac. Select your own A1200 ROM elsewhere.
Leave floppy drives empty. For other setups, attach the HDF as bootable DH0.
It is a plain FFS partition without an RDB: 512-byte blocks, 32 sectors,
1 surface, 2 reserved blocks. Keep it writable to retain scores.

GAME CONTROLS

Joystick in Amiga game port 2: Up/Down accelerates/slows, Left/Right steers.
Fire jumps once you reach 150 km/h. Release Fire between jumps.
Keyboard: arrows or W/A/S/D drive; Space/Ctrl jumps; Return starts/pauses;
Shift is the second original action button; Escape quits to AmigaDOS.
Click the window for keyboard focus.

GAMEPLAY AND PERFORMANCE

Normal gameplay keeps the preceding original-ROM logic, collisions, fuel,
scoring, jump duration, stage progression, hardware sprites and roughly
60.1-Hz game clock. Drawing yields to game logic and event audio. Menus pause
the game clock, so they do not use fuel or create a backlog of game updates.
Continue uses the original game setup path with a reset score and lives.
Paula sound remains an approximation of the source APU; original event
requests and their order are checked against the supplied ROM.

Display frame rate varies in crowded scenes and is lower than the game
update rate. Level-loading pauses remain. This release has been checked in
stock A1200 emulation; physical hardware and a full campaign remain untested.
Verification.json details the tests and their limits.

No Kickstart ROM or Workbench files are included.
Original game: Data East / Vic Tokai. Built from the supplied USA cartridge.
''')
print(O)
