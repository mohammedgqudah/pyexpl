import typing
from abc import ABC, abstractmethod
import subprocess
import tempfile
import pathlib

def nsjail(cmd: list[str]):
    """Build an nsjail command list with the given arguments."""
    return [
        "nsjail",
        "-C",
        "/app/nsjail.cfg",
        "--",
        *cmd
    ]

class RunResult(typing.NamedTuple):
    returncode: int
    stdout: str
    stderr: str

class Runner(ABC):
    @abstractmethod
    def run(self, input: str) -> RunResult:
        pass

class PythonRunner(Runner):
    """
    Run code via a specific python version.
    """
    version: str

    def __init__(self, version: str):
        self.version = version

    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(["/usr/bin/env", f"python{self.version}", "-c", input]),
            capture_output=True,
            input=input,
            text=True,
        )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class MyPyRunner(Runner):
    """
    Run `mypy` against the code.

    Note: I need to figure out how to install typing stubs for inline dependencies when a PEP 723
    script is provided, right now mypy will complain about missing stubs and exit.
    """
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        with tempfile.NamedTemporaryFile("w+") as f:
            _ = f.write(input)
            f.flush()
            process = subprocess.run(
                ["uvx", "mypy", f.name],
                capture_output=True,
                text=True,
            )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class RuffCheckRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            ["uvx", "ruff", "check", "-"],
            capture_output=True,
            input=input,
            text=True,
        )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class RuffFormatRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            ["uvx", "ruff", "format", "-"],
            capture_output=True,
            input=input,
            text=True,
        )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class PyRightRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        with tempfile.NamedTemporaryFile("w+") as f:
            _ = f.write(input)
            f.flush()
            process = subprocess.run(
                ["uvx", "pyright", f.name],
                capture_output=True,
                input=input,
                text=True,
            )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class PyTypeRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        with tempfile.NamedTemporaryFile("w+", suffix=".py") as f:
            _ = f.write(input)
            f.flush()
            process = subprocess.run(
                ["uvx", "--python", "python3.11", "pytype", f.name],
                capture_output=True,
                input=input,
                text=True,
                cwd="/"
            )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

class PyreRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        tmpdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile("w+", dir=tmpdir, suffix=".py") as f:
            _ = f.write(input)
            f.flush()
            process = subprocess.run(
                ["uvx", "--from", "pyre-check", "pyre", "--source-directory", pathlib.Path(f.name).parent],
                capture_output=True,
                input=input,
                text=True,
                cwd="/"
            )
        return RunResult(0, stdout=process.stdout, stderr=process.stderr)

RUNNERS: dict[str, Runner] = {
    "python3.14": PythonRunner("3.14"),
    "python3.13": PythonRunner("3.13"),
    "python3.12": PythonRunner("3.12"),
    "python3.11": PythonRunner("3.11"),
    "python3.10": PythonRunner("3.10"),
    "python3.9": PythonRunner("3.9"),
    "python3.8": PythonRunner("3.8"),
    "mypy": MyPyRunner(),
    "ruff-format": RuffFormatRunner(),
    "ruff-check": RuffCheckRunner(),
    "pyright": PyRightRunner(),
    "pytype": PyTypeRunner(),
    "pyre": PyreRunner(),
}
