# Changelog

## 0.2.3

- Fixed config/options flow so cleared lessons (selection `-` or clear via `x`) are persisted correctly.
- Documented a stable attribute contract for standalone dashboards and an extended set for UI cards.
- Clarified integration + card versioning and compatibility guidance.

## 0.2.0

- Removed the bundled custom Lovelace frontend card completely.
- Simplified the integration to sensor/attribute output only.
- Added flat per-day attributes for standard Lovelace usage without template sensors:
  - `monday_subjects` ... `sunday_subjects`
  - `monday_school_end` ... `sunday_school_end`
- Added grouped helpers:
  - `day_subjects` (dict keyed by `mon`..`sun`)
  - `day_school_end` (dict keyed by `mon`..`sun`)
- Kept all existing detailed attributes unchanged for frontend compatibility.
- Updated documentation and examples for standard Lovelace cards.

## 0.1.5

- Harmonized integration version metadata.
- Refactored config and options flows without changing the stored configuration model.
- Added HACS-friendly frontend asset delivery through the integration package.
- Added repository validation workflows for HACS and Hassfest.
- Reworked README and repository metadata for GitHub/HACS publishing.

## 0.1.4

- Previous internal release.
