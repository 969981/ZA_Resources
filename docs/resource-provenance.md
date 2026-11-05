# Provenance, verification and research evidence

Each original file record should include the version, NCA ID, relative RomFS path, original byte size, original SHA-256, and (where known) first bytes / magic. Each generated artifact records representation, relative destination path, exact byte length and SHA-256.

Archive flow: inventory original → copy small file or 7z-volume large file → calculate artifact SHA-256 → 7z test → save machine-readable manifest → separately restore and compare original SHA-256. A successful archive CRC test does **not** replace original byte-for-byte hash verification.

Research classifications:
- **CONFIRMED** — direct bytes/offsets/hash/native callsites plus reproduction steps.
- **CANDIDATE** — plausible link without authoritative structural or runtime proof.
- **UNKNOWN** — not demonstrated.
- **REJECTED** — disproved with retained supporting evidence.

Avoid publishing guessed file hashes, item types, Pokédex numbers, archive maps or text IDs as established facts. Do not include sensitive local absolute paths in committed manifests.
