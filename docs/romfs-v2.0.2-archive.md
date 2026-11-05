# v2.0.2 RomFS archive and recovery

This page documents the v2.0.2 RomFS import under the NCA folder
4a70b3ff963bfe412681185cea68bf55_NCA. It uses the task-specific 20 MiB
threshold and 45 MiB 7z volumes. The source tree is read-only.

## Representation

- Files smaller than 20 MiB are copied byte-for-byte to the same relative path.
- Files at least 20 MiB are stored as an independent 7z archive beside the
  corresponding relative path. The archive contains only the original basename.
- 7z uses level 5, multiple threads, and 45 MiB volumes. Even a one-volume
  archive is named with the .7z.001 suffix.
- Hidden files and directories are scanned. The scanner excludes .git,
  .za-work, .za-restore, .cache, node_modules and __pycache__ directories,
  plus common temporary and operating-system metadata files. Each exclusion
  is listed in the JSON manifest.
- A destination file with a matching size and SHA-256 is retained. A differing
  destination is preserved and marked Conflict. Partial volume sets are not
  complete; matching staged parts can be resumed, but differing parts are
  never silently replaced.
- Work files stay under .za-work, which is ignored by Git.

## Windows PowerShell usage

Run these commands from Windows PowerShell 5.1 or PowerShell 7 in the
repository. Set SourcePath to the supplied RomFS root and SevenZip to the
Windows 7z.exe installation.

    $repo = (Resolve-Path '.').Path
    $source = '<source RomFS root>'
    $target = Join-Path $repo 'v2.0.2\4a70b3ff963bfe412681185cea68bf55_NCA\1'
    $seven = '<path to Windows 7z.exe>'
    & (Join-Path $repo 'scripts\Archive-ZARomFS.ps1') -SourcePath $source -TargetPath $target -RepositoryRoot $repo -SevenZip $seven -Resume

The archive command writes the requested inventory CSV at
manifests/v2.0.2-romfs-inventory.csv and a detailed machine-readable manifest
at manifests/v2.0.2/transfer_manifest.json. Artifact paths in both manifests
are repository-relative; no source-host absolute path is stored. The CSV target
path points to the copied file or the first .7z volume. Its volume count is
zero for Raw records. The JSON records every archive part's path, byte size
and SHA-256.

To run a read-only archive check without changing files or manifests:

    & (Join-Path $repo 'scripts\Archive-ZARomFS.ps1') -SourcePath $source -TargetPath $target -RepositoryRoot $repo -SevenZip $seven -Resume -VerifyOnly

For the full source-to-destination audit, including 7z integrity and extract
plus SHA-256 checks:

    & (Join-Path $repo 'scripts\Verify-ZARomFS.ps1') -SourcePath $source -TargetPath $target -RepositoryRoot $repo -SevenZip $seven

The full verifier rescans the source, compares source paths, sizes and hashes
against the manifests, checks each volume name and size, runs 7z t, restores
every archive to temporary storage and compares the restored hash. It refreshes
the manifest verification status and exits nonzero if any source or artifact
is missing or inconsistent.

## Restore

Restore one file using the manifest:

    $restore = '<empty restore directory>'
    & (Join-Path $repo 'scripts\Restore-ZARomFS.ps1') -RepositoryRoot $repo -TargetPath $target -DestinationRoot $restore -SourceRelativePath 'arc/data.trpfs' -SevenZip $seven

Restore the entire RomFS, keeping each source-relative subdirectory:

    & (Join-Path $repo 'scripts\Restore-ZARomFS.ps1') -RepositoryRoot $repo -TargetPath $target -DestinationRoot $restore -SevenZip $seven

Restore directly from a first volume when a manifest is unavailable. The script
finds the later volumes in the same directory, checks their sequence, tests the
archive and restores the original basename:

    & (Join-Path $repo 'scripts\Restore-ZARomFS.ps1') -DestinationRoot $restore -ArchiveFirstVolume (Join-Path $target 'arc\data.trpfs.7z.001') -SevenZip $seven

Existing restored files are skipped only when their size and SHA-256 match.
Other existing files are preserved and reported as conflicts.

## Git batch handling

Use Windows-native Git with the existing Windows credential flow. Do not use
Git LFS. Stage only verified artifacts and the manifests for the current batch.
Keep each archive volume intact, and keep each push below GitHub's 2 GiB pack
limit. See [GitHub's push limit guidance](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit).

The first ordinary Git push containing all 87 `arc/data.trpfs` volumes was
rejected with `pack exceeds maximum allowed size (2.00 GiB)`. That unpublished
attempt is retained on the local backup branch
`codex/za-v2.0.2-batch004-failed-attempt`; `master` was returned to the remote
baseline without changing remote history. At the user's direction, the same
verified 45 MiB volumes are now split across these ordinary Git pushes:

| Batch | Volumes | Artifact bytes | Approx. GiB |
| --- | --- | ---: | ---: |
| 004 | 001-032 | 1,509,949,440 | 1.4062 |
| 005 | 033-064 | 1,509,949,440 | 1.4062 |
| 006 | 065-087 | 1,079,831,489 | 1.0057 |

The planned payloads leave margin below 2 GiB for Git pack overhead. The
inventory records `004-006`, and the transfer manifest maps every volume to its
batch. Commit SHAs, actual file counts, and push outcomes are recorded in
`manifests/v2.0.2-git-batches.csv`. Do not start the next batch until the
previous push is confirmed. Never force-push or rewrite remote history.

Do not publish copyrighted source material to a public repository without the
required authorization; private repository visibility does not itself grant
redistribution rights.
