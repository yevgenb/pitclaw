"""Build and test the shared auth policy and production HTTP adapter, without SDL."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
cxx = os.environ.get('CXX', 'c++')
json = root / '.pio/libdeps/wt32_sc01_plus/ArduinoJson/src'
if not json.exists():
    raise SystemExit('Build firmware first to cache ArduinoJson.')
flags = ['-std=c++17', '-O2', '-pthread', '-DSIMULATOR_BUILD', '-DNATIVE_BUILD', '-I' + str(root / 'src'), '-I' + str(json)]
with tempfile.TemporaryDirectory(prefix='pitclaw-auth-tests-') as output:
    out = Path(output)
    mongoose = out / 'mongoose.o'
    subprocess.run([os.environ.get('CC', 'cc'), '-O2', '-c', str(root / 'src/simulator/mongoose.c'), '-o', str(mongoose)], check=True)
    for name, sources in [
        ('peers', ['test/auth/test_peers.cpp']),
        ('policy', ['test/auth/test_auth.cpp', 'src/web_auth.cpp']),
        ('server', ['test/auth/server.cpp', 'src/web_auth.cpp', 'src/web_protocol.cpp', 'src/simulator/sim_web_server.cpp'])
    ]:
        binary = out / name
        subprocess.run([cxx, *flags, *[str(root / source) for source in sources], str(mongoose), '-o', str(binary)], check=True)
        if name in ('peers', 'policy'):
            subprocess.run([str(binary)], check=True, timeout=60)
    subprocess.run(['node', str(root / 'test/auth/test_server.cjs'), str(out / 'server'), str(root / 'data'), str(out)], check=True)
