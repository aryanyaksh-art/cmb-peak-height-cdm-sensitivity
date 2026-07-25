# Environment setup (Windows → WSL)

CLASS supports Linux and macOS. On Windows, run it inside WSL.

## 1. Install WSL

In PowerShell as Administrator:

```powershell
wsl --install -d Ubuntu
```

Reboot if prompted, then set a UNIX username and password when Ubuntu first
launches.

## 2. Build toolchain

`pip install classy` compiles the CLASS C library and a Cython wrapper on your
machine — there are no prebuilt wheels on PyPI. You need a compiler and Python
headers:

```bash
sudo apt update
sudo apt install -y build-essential python3-dev python3-venv gfortran
```

## 3. Virtual environment

Keep the venv in the WSL filesystem, not in the OneDrive folder. Two reasons:
OneDrive will try to sync thousands of compiled artifacts, and `/mnt/c` I/O
under WSL is slow enough to make the CLASS build noticeably worse.

```bash
python3 -m venv ~/venvs/cmb
source ~/venvs/cmb/bin/activate
pip install --upgrade pip
```

## 4. Reach the project folder

The Windows folder is visible from WSL at:

```bash
cd "/mnt/c/Users/aryan/OneDrive/Desktop/CMB dark matter sensitivity study"
```

Consider a symlink so you don't retype it: `ln -s "/mnt/c/Users/.../CMB dark matter sensitivity study" ~/cmb`

## 5. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

The `classy` build takes a few minutes. It compiles the full CLASS C source.

## 6. Verify

```bash
python scripts/00_sanity_check.py
```

Expect a printed classy version of `3.3.4.0` and a positive matter power
spectrum value.

---

## Known failure modes

**`'int_t' is not a type identifier`** — a Cython 3 incompatibility in CLASS
versions before v3.2.4 (fixed Sep 2024). If you somehow land on an old version,
either upgrade or `pip install "Cython<3"` before installing classy. With
3.3.4.0 this should not appear.

**`Package 'python3-venv' has no installation candidate`** — the apt package
list is stale on a fresh WSL install. Run `sudo apt update` first; step 2 above
chains both commands for this reason.

**`pip install -e .` fails with EPERM during `write_pkg_info`** — hit on
2026-07-25, worth knowing about. `/mnt/c` mounts over the 9p protocol without
the `metadata` option, so every file on the Windows drive reports mode 777 and
any `chmod` returns EPERM. setuptools calls `chmod` on a temp file before an
atomic rename, so *any* setuptools build under `/mnt/c` fails the same way, not
just this project. Fix by appending to `/etc/wsl.conf`:

```
[automount]
options = "metadata"
```

Then run `wsl --shutdown` from PowerShell (not `exit` from inside WSL — the VM
has to fully restart for the mount option to apply) and reopen Ubuntu.

**Build fails on a missing compiler** — you skipped step 2, or installed
`build-essential` outside the WSL instance you're actually using.

**`-fopenmp` errors** — a macOS/clang problem, not a WSL one. Shouldn't occur
here.

**ABI mismatch after a NumPy upgrade** — classy is compiled against the NumPy
present at install time. After a NumPy major-version bump, delete the venv and
rebuild rather than upgrading in place.

**Slow first run** — CLASS computes the full Boltzmann hierarchy. A single
lensed spectrum to ℓ=2500 takes on the order of 10–30 seconds. A 16-point sweep
is therefore several minutes; the sweep script caches results to `data/`.
