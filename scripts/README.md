# Local processing tools

The v2.0.2 RomFS scripts support Windows PowerShell 5.1 and PowerShell 7. They use Windows-native file operations and 7-Zip. Pass explicit source, target and repository paths.

- Archive-ZARomFS.ps1 — scan, copy or compress, verify outputs and update the CSV and JSON manifests. Supports -Resume and -VerifyOnly.
- Verify-ZARomFS.ps1 — rescan the source and perform a full artifact audit, including 7z test and restored SHA-256 comparison.
- Restore-ZARomFS.ps1 — restore one source-relative file, the complete RomFS tree, or directly from a .7z.001 file.
- Archive-ZARomFS.Smoke.ps1 — synthetic regression check using temporary files and 1 MiB volumes.

See [v2.0.2 RomFS archive and recovery](../docs/romfs-v2.0.2-archive.md) for commands and safety behavior.

## Internal resource extraction

See [tools](../tools/README.md) and [ZA extraction workflow](../docs/workflows/za-trinity-extraction.md). Run Sync-ZA-Tools.ps1 to verify the six committed pinned source snapshots; Prepare-ZA-Trinity.ps1 to restore verified original files; Run-ZA-TrinityDump.ps1 to index/extract, and Convert-ZA-ExeFS.py for NSO-to-ELF.
