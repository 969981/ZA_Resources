# Layout and naming policy

`v2.0.2/<NCA_ID>_NCA/0/` contains the original ExeFS (`main`, `main.npdm`, `rtld`, `sdk`). Keep the existing files unchanged.

`v2.0.2/<NCA_ID>_NCA/1/` mirrors the original RomFS. Small source files retain their names and bytes. For a source file larger than 90 MiB, publish only `<originalname>.7z.001`, `.002`, ... in its original parent directory. Each archive contains the original filename, not an absolute host path.

`manifests/<version>/transfer_manifest.json` contains original-to-artifact mappings. `docs/` contains Markdown research and workflows; `scripts/` maintained scripts; `tests/` executable synthetic fixtures. Local `.za-work/` and `.za-restore/` are excluded from Git.

Version upgrades create a new `vX.Y.Z/<NCA_ID>_NCA/` tree, not replacements of previous version bytes. Preserve case and spelling of files, including the NCA folder ID.

Important: ordinary Git objects must remain below GitHub's 100 MB file limit; 90 MiB volumes meet the per-blob constraint but are not an endorsement of storing several gigabytes in Git history.
