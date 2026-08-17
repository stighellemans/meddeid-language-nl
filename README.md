# meddeid-language-nl

Dutch language support for MedDeID. The package provides Dutch parsing and
rendering rules, the Belgian-Dutch `nl-BE` post-processing profile, and
versioned Belgian lookup resources used by generation and stability testing.

See the [suite architecture](https://meddeid.github.io/concepts/architecture/)
for how language profiles fit into inference, generation, and evaluation. This
repository is authoritative for Dutch behavior and lookup-resource provenance.

## Installation

```bash
pip install meddeid-language-nl
```

## Usage

```python
from meddeid_language_nl import get_profile

profile = get_profile("nl-BE", version="1")
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

## Subannotation capability

The same repository also contains the optional JavaScript capability
`@meddeid/language-nl/subannotation`. It supplies `nl-BE@1` semantic
subannotation rules, category presentation, formatting policy, and a hashed
resource manifest. `meddeid-subannotate` dynamically resolves this capability;
the application itself remains language-neutral.

The npm package has not been published yet. From a suite source checkout:

```bash
cd ../meddeid-subannotate
npm install --no-save ../meddeid-language-nl
npm run profile -- set nl-BE@1
npm run dev
```

After npm publication, `npm install @meddeid/language-nl` replaces the local
install command. The package registers `nl-BE@1` through
`package.json#meddeid.subannotationProfiles`, so the application does not need
a Dutch-specific resolver branch or a module-path environment variable.

Capability developers can skip installation and persist a direct source path:

```bash
npm run profile -- set nl-BE@1 \
  --module ../meddeid-language-nl/js/subannotation-profile.js
```

The Python and JavaScript packages consume the same files under
`src/meddeid_language_nl/resources/lookup`, so name, street, locality, postal,
and healthcare resources have one authoritative copy and provenance record.

`meddeid-language-nl` is not a recognizer or model and does not include Belgian
DEDUCE. DEDUCE remains an independently licensed comparison system.

## Development

```bash
pip install -e '.[dev]'
pytest
```

Lookup provenance and source-specific terms are documented in
`src/meddeid_language_nl/resources/lookup/SOURCES.md`.

## Licence

Code is AGPL-3.0-only, with incorporated MIT-licensed code identified in
`NOTICE`. Lookup resources retain the terms documented with their source
notice.
