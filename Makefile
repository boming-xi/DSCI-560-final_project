API_DIR=apps/api
WEB_DIR=apps/web

.PHONY: api-install api-dev api-test web-install web-dev up down

api-install:
	cd $(API_DIR) && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

api-dev:
	cd $(API_DIR) && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

api-test:
	cd $(API_DIR) && . .venv/bin/activate && pytest

web-install:
	cd $(WEB_DIR) && npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

up:
	cd infra && docker-compose up -d

down:
	cd infra && docker-compose down

