"""Compile host integration checks against cached firmware dependencies; build firmware first."""
from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
quick=root/'.pio/libdeps/wt32_sc01_plus/QuickPID/src'
json=root/'.pio/libdeps/wt32_sc01_plus/ArduinoJson/src'
flags=['-std=c++17','-I'+str(root/'src'),'-I'+str(root/'test/lid')]
cxx=os.environ.get('CXX','c++')
with tempfile.TemporaryDirectory(prefix='pitclaw-lid-tests-') as out:
    cases=[('engine',['-DARDUINO=100','-I'+str(quick)], [root/'src/pid_controller.cpp',quick/'QuickPID.cpp']),
           ('protocol',['-DNATIVE_BUILD','-I'+str(json)], [root/'src/web_protocol.cpp']),
           ('damper',['-DNATIVE_BUILD'], [])]
    for name,extra,sources in cases:
        binary=Path(out)/name
        subprocess.run([cxx,*flags,*extra,str(root/f'test/lid/test_{name}.cpp'),*map(str,sources),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)
