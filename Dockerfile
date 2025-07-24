FROM python:3.13-alpine AS builder

RUN apk add build-base patchelf ccache
RUN pip install poetry nuitka zstandard

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.in-project true && \
    poetry config virtualenvs.create true && \
    poetry config virtualenvs.path .venv && \
    poetry install

FROM python:3.13-alpine AS final

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

COPY ./src ./src
COPY ./pyproject.toml ./pyproject.toml
COPY ./env.example ./.env

CMD ["/bin/sh", "-c", "source .venv/bin/activate && nb run"]
