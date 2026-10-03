# PyInstaller Windows Build Guide for Agent-Reach

Convert the **Agent-Reach** Python CLI tool into a standalone Windows executable (.exe) using PyInstaller.

## Prerequisites

- **Windows 10/11**
- **Python 3.10+** (add to PATH during installation)
- **pip** (comes with Python)

## Step 1: Clone Agent-Reach Repository

```bash
git clone https://github.com/Panniantong/Agent-Reach.git
cd Agent-Reach
```

## Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
# Install Agent-Reach in development mode
python -m pip install -e .

# Install PyInstaller
pip install pyinstaller

# Install optional dependencies for full features
pip install -e ".[all]"
```

## Step 4: Build Windows Executable with PyInstaller

### Basic Build (Single EXE File)

```bash
pyinstaller --onefile ^
  --name agent-reach ^
  --console ^
  --add-data "agent_reach/skill:agent_reach/skill" ^
  agent_reach/cli.py
```

### Enhanced Build (With Icon & Metadata)

Create an icon file (`.ico`) first, then:

```bash
pyinstaller --onefile ^
  --name agent-reach ^
  --console ^
  --icon=icon.ico ^
  --version-file=version.txt ^
  --add-data "agent_reach/skill:agent_reach/skill" ^
  --hidden-import=agent_reach.channels ^
  --hidden-import=agent_reach.backends ^
  --hidden-import=agent_reach.utils ^
  --collect-all loguru ^
  --collect-all feedparser ^
  --collect-all rich ^
  agent_reach/cli.py
```

### Optimized Build (Smaller Size)

```bash
pyinstaller --onefile ^
  --name agent-reach ^
  --console ^
  --strip ^
  --noupx ^
  --add-data "agent_reach/skill:agent_reach/skill" ^
  --hidden-import=agent_reach.channels ^
  --hidden-import=agent_reach.backends ^
  agent_reach/cli.py
```

## Step 5: Locate the Executable

After building, your `.exe` file will be in:
```
dist/agent-reach.exe
```

## Step 6: Test the Executable

```bash
# Test basic command
dist\agent-reach.exe --version

# Test help
dist\agent-reach.exe --help

# Test doctor (health check)
dist\agent-reach.exe doctor
```

## Step 7: Distribute

1. **Copy `dist/agent-reach.exe`** to any Windows machine (no Python installation needed)
2. **Add to PATH** for system-wide access:
   - Windows + R → `sysdm.cpl` → Environment Variables
   - Add `C:\path\to\dist` to PATH
3. Users can then run: `agent-reach install --env=auto`

---

## Advanced Options

### Spec File Approach (More Control)

Generate a `.spec` file for finer control:

```bash
pyi-makespec --onefile --console ^
  --add-data "agent_reach/skill:agent_reach/skill" ^
  agent_reach/cli.py
```

Edit `agent_reach.spec` to customize, then build:
```bash
pyinstaller agent_reach.spec
```

### Include External Tools

To bundle `yt-dlp` or other dependencies:

```bash
pyinstaller --onefile ^
  --name agent-reach ^
  --console ^
  --add-data "agent_reach/skill:agent_reach/skill" ^
  --hidden-import=yt_dlp ^
  --collect-all yt_dlp ^
  agent_reach/cli.py
```

### Hidden Imports List

Add if PyInstaller misses dependencies:

```bash
--hidden-import=requests ^
--hidden-import=pyyaml ^
--hidden-import=dotenv ^
--hidden-import=pathlib ^
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError" when running .exe

**Solution:** Add `--hidden-import=module_name` for each missing module.

### Issue: .exe runs but displays nothing

**Solution:** Remove `--console` to use GUI mode, or check if processes are being spawned background.

### Issue: File size is too large (>100 MB)

**Solution:** Use `--strip` and `--noupx` flags:
```bash
pyinstaller --onefile --strip --noupx ^
  --name agent-reach agent_reach/cli.py
```

### Issue: Agent-Reach can't find config files

**Solution:** Ensure config path logic handles Windows paths. Agent-Reach uses `~/.agent-reach/` which PyInstaller correctly expands on Windows.

---

## Creating a Windows Installer (Optional)

Use **NSIS** (Nullsoft Scriptable Install System):

1. Install NSIS: https://nsis.sourceforge.io/
2. Create `installer.nsi`:

```nsis
Name "Agent-Reach"
OutFile "Agent-Reach-Installer.exe"
InstallDir "$PROGRAMFILES\AgentReach"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\agent-reach.exe"
  CreateDirectory "$SMPROGRAMS\Agent-Reach"
  CreateShortCut "$SMPROGRAMS\Agent-Reach\Agent-Reach.lnk" "$INSTDIR\agent-reach.exe"
  EnvVarUpdate::AddValue "PATH" "$INSTDIR"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  RMDir /r "$SMPROGRAMS\Agent-Reach"
  EnvVarUpdate::RemoveValue "PATH" "$INSTDIR"
SectionEnd
```

Build:
```bash
makensis installer.nsi
```

---

## Final Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] `pip install pyinstaller`
- [ ] `pip install -e ".[all]"` (Agent-Reach + dependencies)
- [ ] PyInstaller command executed
- [ ] `dist/agent-reach.exe` created
- [ ] Test: `dist\agent-reach.exe --version` works
- [ ] Test: `dist\agent-reach.exe doctor` works
- [ ] Distribute to users

---

## Resources

- **PyInstaller Docs:** https://pyinstaller.org/
- **Agent-Reach GitHub:** https://github.com/Panniantong/Agent-Reach
- **NSIS Installer:** https://nsis.sourceforge.io/
