# Local processing tools

- `Archive-ZAResources.ps1`: import a local RomFS tree, split files larger than the configured threshold with 7z and generate a manifest.
- `Verify-ZAArchives.ps1`: verify artifact sizes, hashes and archive integrity; optional full restore/hash.
- `Restore-ZAResources.ps1`: reconstruct original RomFS relative paths and verify source SHA-256.
- `Publish-ZAArchives.ps1`: plan 500 MiB Git batches; with `-Commit -Push`, stage only manifest-listed artifacts, commit and push without force. Defaults to a read-only plan.

Requirements: Windows PowerShell 5.1+ or PowerShell 7; 7-Zip for nontrivial archive inputs. Run scripts from any directory using explicit `-SourceRomfsRoot` / `-RepositoryRoot` / `-DestinationRoot` parameters. See [archive workflow](../docs/workflows/archive-and-restore.md).
