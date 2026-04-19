API_DIR=apps/api
WEB_DIR=apps/web

.PHONY: api-install api-dev api-test api-seed api-sync-providers api-sync-availability api-import-ca-marketplace web-install web-dev up down

api-install:
	cd $(API_DIR) && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

api-dev:
	cd $(API_DIR) && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

api-test:
	cd $(API_DIR) && . .venv/bin/activate && pytest

api-seed:
	cd $(API_DIR) && . .venv/bin/activate && python -m app.scripts.bootstrap_reference_data

api-sync-providers:
	cd $(API_DIR) && . .venv/bin/activate && python -m app.scripts.sync_providers

api-sync-availability:
	cd $(API_DIR) && . .venv/bin/activate && python -m app.scripts.sync_availability

api-import-ca-marketplace:
	cd $(API_DIR) && . .venv/bin/activate && python -m app.scripts.import_ca_marketplace_plans

web-install:
	cd $(WEB_DIR) && npm install

web-dev:
	cd $(WEB_DIR) && npm run dev

up:
	cd infra && docker-compose up -d

down:
	cd infra && docker-compose down
