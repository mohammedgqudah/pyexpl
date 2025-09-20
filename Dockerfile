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

# -------------------------------------------
FROM buildpack-deps:bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project


# jail root
RUN mkdir -p /pyexplroot/home/.local/share/uv/python
RUN mkdir -p /pyexplroot/home/.local/bin
RUN mkdir -p /pyexplroot/home/.cache/uv
RUN mkdir -p /pyexplroot/home/pyexpl
RUN mkdir -p /pyexplroot/home/pythons

RUN uv python install python3.13.7 --install-dir /pyexplroot/home/pythons --no-bin
RUN uv python install python3.12.11 --install-dir /pyexplroot/home/pythons --no-bin
RUN uv python install python3.11.13 --install-dir /pyexplroot/home/pythons --no-bin
RUN uv python install python3.10.18 --install-dir /pyexplroot/home/pythons --no-bin
RUN uv python install python3.9.23 --install-dir /pyexplroot/home/pythons --no-bin
RUN uv python install python3.8.20 --install-dir /pyexplroot/home/pythons --no-bin

RUN ln -s /usr/bin/python3 /usr/bin/python 
ADD . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked


# nsjail
COPY --link --from=nsjail /nsjail/nsjail /usr/sbin/
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libprotobuf.so.32 /lib/x86_64-linux-gnu/libprotobuf.so.32
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-route-3.so.200 /lib/x86_64-linux-gnu/libnl-route-3.so.200
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-route-3.so.200 /lib/x86_64-linux-gnu/libnl-route-3.so.200
COPY --link --from=nsjail /lib/x86_64-linux-gnu/libnl-3.so.200 /lib/x86_64-linux-gnu/libnl-3.so.200
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# all traversting /root so that nsjail can mount /root/.local/share/uv/python
RUN chmod o+x /root
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
CMD ["uv", "run", "pyexpl"]
