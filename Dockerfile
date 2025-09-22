# build nsjail ------------------------------
FROM buildpack-deps:bookworm AS nsjail

WORKDIR /nsjail

RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \
        bison\
        flex \
        libprotobuf-dev\
        libnl-route-3-dev \
        protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

RUN git clone -b master --single-branch https://github.com/google/nsjail.git . \
    && git checkout be4475f86303eb3ffd3bedc253091dc3e7e71bff
RUN make

# final layer -------------------------------
FROM buildpack-deps:bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# jail root
RUN mkdir -p /pyexplroot/home/pyexpl
RUN mkdir -p /pyexplroot/home/pythons

# sync pyexpl
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# install python versions and tools
RUN --mount=type=cache,target=/root/.cache/uv \
	uv python install python3.14.0rc2 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.13.7 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.12.11 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.11.13 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.10.18 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.9.23 --install-dir /pyexplroot/home/pythons --no-bin \
	&& uv python install python3.8.20 --install-dir /pyexplroot/home/pythons --no-bin
# install ruff
RUN --mount=type=cache,target=/root/.cache/uv \
	UV_PYTHON="/pyexplroot/home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13" \
	UV_TOOL_DIR="/pyexplroot/home/tools" \
	uv --no-managed-python tool install ruff --force

# install mypy
RUN --mount=type=cache,target=/root/.cache/uv \
	UV_PYTHON="/pyexplroot/home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13" \
	UV_TOOL_DIR="/pyexplroot/home/tools" \
	uv --no-managed-python tool install mypy --force

# install pyright
RUN --mount=type=cache,target=/root/.cache/uv \
	UV_PYTHON="/pyexplroot/home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13" \
	UV_TOOL_DIR="/pyexplroot/home/tools" \
	uv --no-managed-python tool install pyright[nodejs] --force

# install pytype
RUN --mount=type=cache,target=/root/.cache/uv \
	UV_PYTHON="/pyexplroot/home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12" \
	UV_TOOL_DIR="/pyexplroot/home/tools" \
	uv --no-managed-python tool install pytype --force

# install pyre
RUN --mount=type=cache,target=/root/.cache/uv \
	UV_PYTHON="/pyexplroot/home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13" \
	UV_TOOL_DIR="/pyexplroot/home/tools" \
	uv --no-managed-python tool install pyre-check --force

# create symlinks that will work inside the jail
RUN ln -s -f /home/pythons/cpython-3.14.0rc2-linux-x86_64-gnu/bin/python3.14 /usr/bin/python3.14
RUN ln -s -f /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /usr/bin/python3.13
RUN ln -s -f /home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12 /usr/bin/python3.12
RUN ln -s -f /home/pythons/cpython-3.11.13-linux-x86_64-gnu/bin/python3.11 /usr/bin/python3.11
RUN ln -s -f /home/pythons/cpython-3.10.18-linux-x86_64-gnu/bin/python3.10 /usr/bin/python3.10
RUN ln -s -f /home/pythons/cpython-3.9.23-linux-x86_64-gnu/bin/python3.9 /usr/bin/python3.9
RUN ln -s -f /home/pythons/cpython-3.8.20-linux-x86_64-gnu/bin/python3.8 /usr/bin/python3.8

# adjust mypy
# change pyvenv.cfg:home to work inside the jail
RUN sed -i 's|^home = .*|home = /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin|' /pyexplroot/home/tools/mypy/pyvenv.cfg
# update symlinks
RUN cd /pyexplroot/home/tools/mypy/bin/ && rm -f python3 python3.13 python
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/mypy/bin/python3.13
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/mypy/bin/python3
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/mypy/bin/python
# update shebang
RUN sed -i '1s|.*|#!/home/tools/mypy/bin/python|' /pyexplroot/home/tools/mypy/bin/mypy

# adjust PYRE
# change pyvenv.cfg:home to work inside the jail
RUN sed -i 's|^home = .*|home = /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin|' /pyexplroot/home/tools/pyre-check/pyvenv.cfg
# update symlinks
RUN cd /pyexplroot/home/tools/pyre-check/bin/ && rm -f python3 python3.13 python
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyre-check/bin/python3.13
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyre-check/bin/python3
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyre-check/bin/python
# update shebang
RUN sed -i '1s|.*|#!/home/tools/pyre-check/bin/python|' /pyexplroot/home/tools/pyre-check/bin/pyre

# adjust pyright
# change pyvenv.cfg:home to work inside the jail
RUN sed -i 's|^home = .*|home = /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin|' /pyexplroot/home/tools/pyright/pyvenv.cfg
# update symlinks
RUN cd /pyexplroot/home/tools/pyright/bin/ && rm -f python3 python3.13 python
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyright/bin/python3.13
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyright/bin/python3
RUN ln -s /home/pythons/cpython-3.13.7-linux-x86_64-gnu/bin/python3.13 /pyexplroot/home/tools/pyright/bin/python
# update shebang
RUN sed -i '1s|.*|#!/home/tools/pyright/bin/python|' /pyexplroot/home/tools/pyright/bin/pyright


# adjust pytype
# change pyvenv.cfg:home to work inside the jail
RUN sed -i 's|^home = .*|home = /home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin|' /pyexplroot/home/tools/pytype/pyvenv.cfg
# update symlinks
RUN cd /pyexplroot/home/tools/pytype/bin/ && rm -f python3 python3.12 python
RUN ln -s /home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12 /pyexplroot/home/tools/pytype/bin/python3.12
RUN ln -s /home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12 /pyexplroot/home/tools/pytype/bin/python3
RUN ln -s /home/pythons/cpython-3.12.11-linux-x86_64-gnu/bin/python3.12 /pyexplroot/home/tools/pytype/bin/python
# update shebang
RUN sed -i '1s|.*|#!/home/tools/pytype/bin/python|' /pyexplroot/home/tools/pytype/bin/pytype
RUN sed -i '1s|.*|#!/home/tools/pytype/bin/python|' /pyexplroot/home/tools/pytype/bin/pytype-single

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# nsjail
COPY --link --from=nsjail /nsjail/nsjail /usr/sbin/
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libprotobuf.so.32 /lib/x86_64-linux-gnu/libprotobuf.so.32
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-route-3.so.200 /lib/x86_64-linux-gnu/libnl-route-3.so.200
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-route-3.so.200 /lib/x86_64-linux-gnu/libnl-route-3.so.200
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-3.so.200 /lib/x86_64-linux-gnu/libnl-3.so.200
#COPY --link --from=builder /lib/x86_64-linux-gnu/libz.so.1 /lib/x86_64-linux-gnu/

COPY jail_entrypoint.sh /pyexplroot/home/
COPY wrapstdin.sh /pyexplroot/home/
RUN chmod +x /pyexplroot/home/jail_entrypoint.sh
RUN chmod +x /pyexplroot/home/wrapstdin.sh


WORKDIR /app
CMD ["uv", "run", "pyexpl"]
