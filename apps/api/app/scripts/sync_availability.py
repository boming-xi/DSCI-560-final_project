from __future__ import annotations

from app.api.deps import get_availability_sync_service


def main() -> None:
    result = get_availability_sync_service().sync()
    print(
        "Availability sync completed:",
        {
            "source": result.source,
            "mode": result.mode,
            "slots_upserted": result.slots_upserted,
            "reference_data_backend": result.reference_data_backend,
        },
    )


if __name__ == "__main__":
    main()
