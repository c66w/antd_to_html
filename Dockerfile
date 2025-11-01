FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY .env ./.env

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
 && pip install --upgrade pip \
 && pip install --no-cache-dir -e .

COPY schema.sql ./schema.sql

ENV PORT=8400
EXPOSE 8400

CMD ["uvicorn", "antd_to_html.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8400"]
