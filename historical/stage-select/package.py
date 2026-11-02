from pathlib import Path
import subprocess,os,shutil,json,hashlib
R=Path(__file__).resolve().parent;root=R/'hdf-root';(root/'C').mkdir(parents=True,exist_ok=True);(root/'S').mkdir(exist_ok=True)
(root/'S/Startup-Sequence').write_text('C:BumpNJump\n')
shutil.copyfile(R/'build/BumpNJump',root/'C/BumpNJump')
env=dict(os.environ);env['PYTHONPATH']='/path/to/local-user/Documents/Codex/2026-10-06/task-3/private/tools/amitools'
hdf=R/'build/BumpNJump-A1200.hdf'
if hdf.exists():hdf.unlink()
r=subprocess.run(['python3','-m','amitools.tools.xdftool',str(hdf),'pack',str(root),'DOS1','size=8Mi','+','boot','install'],env=env,capture_output=True,text=True);assert not r.returncode,r.stdout+r.stderr
T=R/'test';T.mkdir(exist_ok=True)
for name in ['base','state','logs','cache','screenshots','config','kickstarts','controllers','themes','disks','hard-drives','cdroms','userdata','userconfig','usercache','temp','results']:(T/name).mkdir(exist_ok=True)
s=f'''[fs-uae]
amiga_model = A1200
cpu = 68EC020
chip_memory = 2048
slow_memory = 0
fast_memory = 0
zorro_iii_memory = 0
accelerator = none
jit_compiler = 0
accuracy = 1
uae_cpu_speed = real
uae_cpu_multiplier = 4
kickstart_file = /Applications/AmigaVision-2025.05.05/Kickstart v3.1 rev 40.68 (1993)(Commodore)(A1200)[!].rom
fullscreen = 0
initial_input_grab = 0
automatic_input_grab = 0
window_width = 960
window_height = 720
texture_filter = nearest
keep_aspect = 1
scanlines = 0
volume = 80
console_debugger = 1
uaem_write_flags = 0
floppy_drive_count = 0
hard_drive_0 = {hdf}
hard_drive_0_type = hdf
hard_drive_0_read_only = 1
hard_drive_1 = {T/'results'}
hard_drive_1_label = DH1
hard_drive_1_priority = -128
joystick_port_1 = keyboard
keyboard_key_f9 = action_enter_debugger
keyboard_key_q = action_joy_1_fire_button
config_window_title = Bump n Jump - stock A1200 test
base_dir = {T/'base'}
state_dir = {T/'state'}
logs_dir = {T/'logs'}
cache_dir = {T/'cache'}
screenshots_dir = {T/'screenshots'}
configurations_dir = {T/'config'}
save_states_dir = {T/'state'}
kickstarts_dir = {T/'kickstarts'}
controllers_dir = {T/'controllers'}
themes_dir = {T/'themes'}
floppies_dir = {T/'disks'}
hard_drives_dir = {T/'hard-drives'}
cdroms_dir = {T/'cdroms'}
'''
(T/'test.fs-uae').write_text(s)
print('HDF',hdf.stat().st_size,hashlib.sha256(hdf.read_bytes()).hexdigest())
