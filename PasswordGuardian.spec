# PyInstaller recipe for the booth build: dist/PasswordGuardian/PasswordGuardian.exe plus an _internal folder.
# Build on Windows with build_exe.bat; Arcade ships its own PyInstaller hook for its shaders and pymunk.
from pathlib import Path

root = Path(SPECPATH)
datas = [(str(root / "assets/images"), "assets/images"), (str(root / "assets/fonts"), "assets/fonts"),
         (str(root / "data"), "data"), (str(root / "assets/LICENSES.md"), "assets")]

a = Analysis([str(root / "run_game.py")], pathex=[str(root / "src")], datas=datas)
# Arcade's hook files VERSION as a folder (arcade/VERSION/VERSION); arcade reads it as a file.
a.datas = [("arcade/VERSION", src, kind) if dest.replace("\\", "/") == "arcade/VERSION/VERSION" else (dest, src, kind)
           for dest, src, kind in a.datas]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PasswordGuardian",
          console=False)  # no black console window next to the game
coll = COLLECT(exe, a.binaries, a.datas, name="PasswordGuardian")
