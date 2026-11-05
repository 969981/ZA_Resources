# ZA_Resources

Pokemon Legends: Z-A executable, archive-inventory and resource-format research workspace. Initial input: v2.0.2. Existing ExeFS files and their inventory remain under their original NCA hierarchy.

## Start here

- [Repository structure](docs/repository-layout.md)
- [File provenance and evidence](docs/resource-provenance.md)
- [v2.0.2 RomFS archive and recovery](docs/romfs-v2.0.2-archive.md)
- [Scripts](scripts/README.md)
- [Pinned ZA tools](tools/README.md)
- [Trinity/ELF extraction](docs/workflows/za-trinity-extraction.md)
- [Research notes](docs/research/v2.0.2/README.md)
- [Agent instructions](AGENTS.md)

## Current source layout

- v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/0/ — original ExeFS files; preserve their names and bytes.
- v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/ — RomFS destination. For this v2.0.2 import, files smaller than 20 MiB are raw and files at least 20 MiB use independent 45 MiB 7z volumes.
- manifests/v2.0.2-romfs-inventory.csv — requested CSV inventory.
- manifests/v2.0.2/transfer_manifest.json — per-artifact path, size and SHA-256 details.
- manifests/v2.0.2-git-batches.csv — commit and push records for resource batches.

The source dataset must be supplied locally. Review the archive workflow and repository visibility before pushing source material.

## Data handling

Keep source files read-only. Verify every copy or archive before staging. Stage only explicit, verified paths in batches. Never commit decryption keys. GitHub has per-object and per-push limits; do not split one source file's volumes across commits. Use approved external storage if an indivisible file group cannot fit the GitHub limits.
