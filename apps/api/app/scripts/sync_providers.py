from __future__ import annotations

from app.api.deps import get_provider_sync_service


def main() -> None:
    result = get_provider_sync_service().sync()
    print(
        "Provider sync completed:",
        {
            "source": result.source,
            "mode": result.mode,
            "clinics_upserted": result.clinics_upserted,
            "doctors_upserted": result.doctors_upserted,
            "reference_data_backend": result.reference_data_backend,
        },
    )


if __name__ == "__main__":
    main()
