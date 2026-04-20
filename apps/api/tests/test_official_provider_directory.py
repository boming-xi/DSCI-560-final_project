from app.core.config import get_settings
from app.integrations.provider_directory_verification.base import OfficialDirectoryMatch
from app.repositories.doctor_repo import DoctorRepository
from app.repositories.insurance_repo import InsuranceRepository
from app.services.insurance_network_service import InsuranceNetworkService
from app.services.insurance_service import InsuranceService


class FakeOfficialProviderDirectoryService:
    def __init__(self, match: OfficialDirectoryMatch | None) -> None:
        self.match = match

    def has_live_client(self, plan_context: object) -> bool:
        return True

    def verify(self, **_: object) -> OfficialDirectoryMatch | None:
        return self.match


def _build_network_service(
    match: OfficialDirectoryMatch | None,
) -> tuple[InsuranceNetworkService, DoctorRepository]:
    settings = get_settings()
    insurance_service = InsuranceService(InsuranceRepository(settings))
    doctor_repo = DoctorRepository(settings)
    network_service = InsuranceNetworkService(
        insurance_service,
        official_provider_directory_service=FakeOfficialProviderDirectoryService(match),
    )
    return network_service, doctor_repo


def test_official_directory_match_wins_when_live_official_check_succeeds() -> None:
    network_service, doctor_repo = _build_network_service(
        OfficialDirectoryMatch(
            label="Verified by official directory",
            reason="Matched the doctor in a live carrier provider directory feed.",
            evidence=["Matched doctor name, specialty, and clinic ZIP in carrier directory."],
            network_url="https://carrier.example.com/find-care",
            source="official_provider_directory_api:test-carrier",
        )
    )
    doctor = doctor_repo.get_doctor("ucla-ryan-aronin")
    clinic = doctor_repo.get_clinic("clinic-ucla-westwood")
    assert doctor is not None
    assert clinic is not None

    plan_context, _summary = network_service.resolve_plan_context(
        selected_plan_id="70285CA8040016",
        doctor_search_plan_id=None,
        insurance_query="Blue Shield of California Gold 80 Trio HMO",
    )

    verification = network_service.build_verification(doctor, clinic, plan_context)

    assert verification is not None
    assert verification.status == "verified"
    assert verification.source == "official_provider_directory_api:test-carrier"
    assert verification.network_url == "https://carrier.example.com/find-care"


def test_official_only_mode_returns_uncertain_when_live_directory_has_no_match() -> None:
    network_service, doctor_repo = _build_network_service(None)
    doctor = doctor_repo.get_doctor("ucla-ryan-aronin")
    clinic = doctor_repo.get_clinic("clinic-ucla-westwood")
    assert doctor is not None
    assert clinic is not None

    plan_context, _summary = network_service.resolve_plan_context(
        selected_plan_id="70285CA8040016",
        doctor_search_plan_id=None,
        insurance_query="Blue Shield of California Gold 80 Trio HMO",
    )

    verification = network_service.build_verification(doctor, clinic, plan_context)

    assert verification is not None
    assert verification.status == "uncertain"
    assert verification.source == "official_ca_marketplace_catalog"
    assert any("A live carrier provider directory was queried and did not confirm this doctor." in item for item in verification.evidence)
