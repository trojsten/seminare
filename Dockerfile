FROM node:21.7.1-alpine AS cssbuild

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && \
 pnpm install

COPY ./ /app
COPY tailwind.config.js ./
RUN pnpm run build
CMD ["pnpm", "run", "watch"]

FROM ghcr.io/trojsten/django-docker:v6

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY --chown=appuser:appuser ./ /app
COPY --chown=appuser:appuser --from=cssbuild /app/seminare/style/static/* /app/seminare/style/static/

RUN uv run pygmentize -S monokai -f html -a .codehilite >/app/seminare/style/static/code.css
RUN DATABASE_URL=sqlite://:memory: JUDGE_TOKEN=dummy python manage.py collectstatic --no-input
ENV BASE_START=/app/entrypoint.sh
