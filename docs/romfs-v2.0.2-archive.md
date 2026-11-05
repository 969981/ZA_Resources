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

Stage explicit verified artifacts and the corresponding manifests only. Keep
all volumes for one source file in a single commit. Record each commit SHA,
artifact count, byte count and push status in the manifests/v2.0.2-git-batches.csv ledger, and
write its batch number into the inventory CSV.

Keep each batch near 400 MiB and below 200 files where possible. A file group
larger than those targets must not be divided. GitHub also enforces a 2 GiB
limit on one push; if an indivisible file group exceeds that limit, do not push
or split it across commits under this workflow. Use only an approved storage
method after checking access, rights and any account quota. See
[GitHub's push limit guidance](https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit).

Do not force-push or rewrite history. Recheck the current branch and remote
head before every push. Do not publish copyrighted source material to a public
repository without the required authorization; private repository visibility
does not itself grant redistribution rights.
