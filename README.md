# ZA_Resources

Pokémon Legends: Z-A executable, archive-inventory and resource-format research workspace. Initial input: **v2.0.2**. The existing ExeFS files and inventory are preserved under their original NCA hierarchy.

## Start here
- [Repository structure](docs/repository-layout.md)
- [File provenance and evidence](docs/resource-provenance.md)
- [M1: 7-Zip archive workflow](docs/workflows/archive-and-restore.md)
- [Scripts](scripts/README.md)
- [Research notes](docs/research/v2.0.2/README.md)
- [Agent instructions](AGENTS.md)

## Current source layout
- `v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/0/` — original ExeFS files; do not rename.
- `v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/v2.0.2_file_inventory.csv` — original exported file inventory.
- `.../1/` — intended RomFS destination with source-relative paths; large originals are represented by 90 MiB 7z volumes **only after a local import**.
- `manifests/v2.0.2/transfer_manifest.json` — generated locally by the archiver after import; not yet present until M1 is run.

The repository **does not claim the RomFS archive has already been uploaded**. The local original dataset must be supplied by the operator.

## Data handling
Keep source files read-only. Archive to a separate local clone, verify all artifacts, then stage explicit paths in sensible batches. Never commit decryption keys. GitHub has per-blob and repository-size constraints; large or copyrighted source assets may be better stored in authorized private object storage while keeping manifests and tools here.
