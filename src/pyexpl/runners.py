import typing
from abc import ABC, abstractmethod
import subprocess


def nsjail(cmd: list[str], jail_opts: list[str] | None = None):
    jail_opts = jail_opts or []
    """Build an nsjail command list with the given arguments."""
    return ["nsjail", "-C", "/app/nsjail.cfg", *jail_opts, "-q", "--", *cmd]


class RunResult(typing.NamedTuple):
    returncode: int
    stdout: str


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
        process = subprocess.Popen(
            nsjail(["/usr/bin/env", f"python{self.version}", "-c", input]),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        # TODO: make this configurable
        MAX = 10000
        chunk_size = 100
        stdout = ""

        # We can't wait for the process to finish before reading stdout or else
        # a jailed process can consume all of the host memory by filling up the stdout buffer. Instead, read
        # stdout one chunk at a time and terminate nsjail if the the process exceeds the limit.
        while process.poll() is None:
            stdout_chunk = process.stdout.read(chunk_size)
            if len(stdout) + len(stdout_chunk) > MAX:
                stdout += "\n[Output truncated]"
                break
            stdout += stdout_chunk

        process.terminate()

        return RunResult(
            143 if process.returncode is None else process.returncode, stdout=stdout
        )


class MyPyRunner(Runner):
    """
    Run `mypy` against the code.

    Note: I need to figure out how to install typing stubs for inline dependencies when a PEP 723
    script is provided, right now mypy will complain about missing stubs and exit.
    """

    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(
                [
                    "/home/tools/mypy/bin/python",
                    "/home/tools/mypy/bin/mypy",
                    "-c",
                    input,
                ],
                [
                    "--cgroup_cpu_ms_per_sec",
                    "0",
                ],
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return RunResult(0, stdout=process.stdout)


class RuffCheckRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(["/usr/bin/env", "ruff", "check", "-"]),
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return RunResult(0, stdout=process.stdout)


class RuffFormatRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(["/usr/bin/env", "ruff", "format", "-"]),
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return RunResult(0, stdout=process.stdout)


class PyRightRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(["/home/wrapstdin.sh", "/usr/bin/env", "pyright"]),
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return RunResult(0, stdout=process.stdout)


class PyTypeRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(
                ["/home/wrapstdin.sh", "/usr/bin/env", "pytype-single"],
                # pytype doesn't like being in the jail for some reason and will not always work
                # if I limit cpu time.
                [
                    "--cgroup_mem_max",
                    "0",
                    "--cgroup_cpu_ms_per_sec",
                    "0",
                    "--rlimit_nofile",
                    "1000",  # not sure why it needs to open lots of files
                ],
            ),
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return RunResult(0, stdout=process.stdout)


class PyreRunner(Runner):
    def run(self, input: str) -> RunResult:  # pyright: ignore[reportImplicitOverride]
        process = subprocess.run(
            nsjail(
                [
                    "/home/wrapstdin.sh",
                    "-d",
                    "/usr/bin/env",
                    "pyre",
                    "--noninteractive",
                    "--source-directory",
                ],
                [
                    # pyre mmap's 9GB of NORESERVE memory.
                    "--rlimit_as",
                    "99999999999999999",
                ],
            ),
            input=input,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return RunResult(0, stdout=process.stdout)


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
