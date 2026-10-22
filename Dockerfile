FROM helsinki.azurecr.io/ubi9/python-312-gdal

COPY --from=ghcr.io/astral-sh/uv:0.13.5@sha256:32a7bb39b496babbd997b0a39a4d66c126bdaf5661b302bf6f06abda8deca6ff /uv /uvx /usr/local/bin/

ENV UV_PROJECT_ENVIRONMENT=/opt/app-root \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never

ENV PATH="/opt/app-root/bin:${PATH}"

RUN dnf update -y

WORKDIR /usr/src/app

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-default-groups --group prod

COPY . .

USER nobody:0

EXPOSE 8080

ENTRYPOINT ["./docker-entrypoint.sh"]
