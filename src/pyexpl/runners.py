import typing
from abc import ABC, abstractmethod
import subprocess
import tempfile

def nsjail(cmd: list[str]):
    """Build an nsjail command list with the given arguments."""
    return [
        "nsjail",
        "--quiet",
        "-C",
        "nsjail.cfg",
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
    Run code via a specific python version using `uv --python`.

    The python version must be installed on the host because the `uv` cache inside
    the jail is a read-only mount, so `uv` will be unable to install python versions on-demand.
    
    This will attempt to run the program as a PEP 723 script (inline metadata), which means
    if internet is enabled inside the jail you can install dependencies.
    """
    version: str

    def __init__(self, version: str):
        self.version = version

    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(["/usr/bin/env", "uv", "run", "--python", f"python{self.version}", "--script", "-"]),
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
}
