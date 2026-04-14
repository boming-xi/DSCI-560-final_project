from __future__ import annotations

from app.core.config import get_settings
from app.db.bootstrap import bootstrap_reference_data


def main() -> None:
    settings = get_settings()
    succeeded = bootstrap_reference_data(settings)
    if succeeded:
        print(f"Reference data synchronized into {settings.postgres_url}.")
    else:
        print("Database unavailable; reference data remained on JSON fallback.")


if __name__ == "__main__":
    main()
