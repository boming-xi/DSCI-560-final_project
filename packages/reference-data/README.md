# Reference Data

This folder replaces the older `mock-data` label because the project now uses a mix of:

- official-derived plan data
- curated official-provider reference records
- optional connector snapshots for local sync and testing

Current files:

- `ca_marketplace_plans.json`
  California marketplace plan data derived from official public plan files.
- `doctors.json`
  Current doctor reference set used by the API. The live ranking flow only surfaces doctors with official public profile and booking links.
- `clinics.json`
  Clinic reference data paired with the doctor records.
- `insurance_plans.json`
  Internal normalized insurance records used for legacy matching and compatibility layers.
- `insurance_advisor_catalog.json`
  Additional plan-advisor support data.
- `provider_directory_snapshot.json`
  Optional local snapshot fixture for provider sync development.
- `provider_availability_snapshot.json`
  Optional local snapshot fixture for availability sync development.

So the folder is no longer “all mock data,” but it is also not “all live API output.” It is best described as the project's checked-in reference data.
