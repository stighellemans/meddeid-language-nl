# Changelog

All notable user-visible changes are recorded here. This project follows
semantic versioning while pre-1.0 versions may still refine public contracts.

## [0.2.0] - 2026-08-27

- Removed the manually incremented Dutch subannotation ruleset version;
  releases and Git history now provide its change history.
- Moved all preprocessing seeds outside the Dutch benchmark label namespace,
  added automatic profession handling, and retained both `province` and
  `region` because both occur in the decisive Dutch synthetic gold data.
- Connected Dutch date/age parsing and rendering to the suite-wide declarative
  age policy and added trusted full birth-date variants for `nl-BE` and `nl-NL`.

## [0.1.1] - 2026-08-17

- Published the first externally supported MedDeID Dutch language profile release.
- Added public installation, compatibility, licensing, and verification
  metadata.
- Established independent CI and immutable release artifacts.

For earlier migration history, consult the repository's Git history.
