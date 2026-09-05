# meddeid-language-nl

Dutch language support for MedDeID. The package provides shared Dutch parsing
and rendering rules plus profile-scoped resources for Belgium (`nl-BE`) and
the Netherlands (`nl-NL`). Both profiles are designed for the same Dutch
recognizer model.

See the [suite architecture](https://stighellemans.github.io/meddeid/concepts/architecture/)
for how language profiles fit into inference, generation, and evaluation. This
repository is authoritative for Dutch behavior and lookup-resource provenance.

## Installation

```bash
pip install meddeid-language-nl
```

## Usage

```python
from meddeid_language_nl import get_profile

profile = get_profile("nl-NL")
spans = profile.post_process_spans(raw_spans, text, metadata)
run_manifest["language_profile"] = profile.manifest()
```

The profile manifest records the profile contract together with the SHA-256
digest and value count of each lookup file. Generation, training, inference,
and evaluation runs can therefore identify the exact locale resources used.

The package registers its profile provider in the
`meddeid.language_profiles` Python entry-point group. Other language packages
can implement the same provider interface without changing the inference
package.

Dutch date parsing and wording use the one age-granularity policy loaded by
the MedDeID engine. The package does not define separate Dutch age bands. It
also expands a trusted full `patient.birth_date` into bounded `nl-BE`/`nl-NL`
representations for deterministic span recovery.

## Subannotation capability

The same repository also contains optional JavaScript capabilities for
`nl-BE` and `nl-NL`. They share one rule engine while loading the selected
profile's names, addresses, and institutions. `meddeid-subannotate` dynamically
resolves the capability; the application itself remains language-neutral.

Install the published JavaScript capability from npm and select it in a
`meddeid-subannotate` workspace:

```bash
npm install --no-save @meddeid/language-nl@0.2.1
npm run profile -- set nl-BE nl-NL
npm run dev
```

The package registers both profiles through
`package.json#meddeid.subannotationProfiles`, so the application does not need
a Dutch-specific resolver branch or a module-path environment variable.

Capability developers can skip installation and persist a direct source path:

```bash
npm run profile -- set nl-NL \
  --module ../meddeid-language-nl/js/subannotation-nl-nl.js
```

The Python and JavaScript packages consume the same files under
`src/meddeid_language_nl/resources/<profile>/lookup`, so name, street,
locality, postal, and healthcare resources have authoritative, locale-scoped
copies and provenance records.

`meddeid-language-nl` is not a recognizer or model and does not include Belgian
DEDUCE. DEDUCE remains an independently licensed comparison system.

## Development

```bash
pip install -e '.[dev]'
pytest
```

Lookup provenance and source-specific terms are documented in
`src/meddeid_language_nl/resources/<profile>/lookup/SOURCES.md`.

## Licence

Code is AGPL-3.0-only, with incorporated MIT-licensed code identified in
`NOTICE`. Lookup resources retain the terms documented with their source
notice.
