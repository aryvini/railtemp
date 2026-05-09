# railtemp

[![Python application](https://github.com/aryvini/railtemp/actions/workflows/release.yml/badge.svg?branch=master)](https://github.com/aryvini/railtemp/actions/workflows/python-app.yml)



Module to simulate railway temperatures based on weather parameters, such as: wind velocity, air temperature and solar radiation.

## Instalation

```shell
uv pip install git+https://github.com/aryvini/railtemp.git
```

### Optional Rust backend (experimental)

The Rust backend is **optional** and currently **experimental**.
It is currently available on the **develop** branch.
Published wheel assets are marked as **pre-release** in GitHub Releases, and are not stable releases yet.

If you do not install it, simulations continue to run with the default Python backend.

Wheel files are published in **GitHub Releases** (release assets):

https://github.com/aryvini/railtemp/releases

Download the wheel that matches your Python version and platform.
File names look like:

```text
railtemp-1.3.0.dev2-cp312-cp312-linux_x86_64.whl
```

How to choose the correct wheel:

- Python version: use the `cpXYZ` tag.
- `cp310` = Python 3.10
- `cp311` = Python 3.11
- `cp312` = Python 3.12
- `cp313` = Python 3.13
- OS/platform (last wheel tag):
- Linux (64-bit): `linux_x86_64` or `manylinux*_x86_64`
- Linux (ARM64): `linux_aarch64` or `manylinux*_aarch64`
- macOS Intel: `macosx_*_x86_64`
- macOS Apple Silicon: `macosx_*_arm64`
- Windows (64-bit): `win_amd64`

Example: if you are on Linux 64-bit with Python 3.12, pick a wheel containing `cp312` and `linux_x86_64` (or `manylinux` for x86_64).

Install from the downloaded wheel file:

```shell
uv pip install /path/to/<wheel-file-name>.whl
```

Run a simulation with the Rust backend:

```python
simu.run(Trail_initial=25.0, backend="rust")
```

### Build from source (local development)

If you want to develop locally instead of using release wheels, build from source:

```shell
# Clone repository
git clone https://github.com/aryvini/railtemp.git
cd railtemp

# Create environment and install dependencies (including dev tools)
uv venv
uv sync --dev

# Build and install Rust extension in the uv environment
uv run maturin develop --release
```

Quick check after build:

```shell
uv run python -c "import railtemp._core; print('Rust backend available')"
```

## About
The code presented here is subjected of a Master Thesis work developed at [Instituto Politécnico de Bragança - Portugal](http://portal3.ipb.pt/index.php/pt/). Detailed publication is available [here](https://bibliotecadigital.ipb.pt/handle/10198/23684). The research is based on a previous model developed by Chungnam National University, that can be found [here](https://doi.org/10.1007/s12541-019-00015-1).

The purpose of the code is to facilitate the process of simulate/calculate a heat transfer equation varying many parameters such as: geolocation, profile, physical aspects and more. Therefore this module abstract the process of solving into some easy classes' methods.

Examples are available [here](./examples/).


In case of any issue or question, feel free to contact me: aryviniciusnf@gmail.com

