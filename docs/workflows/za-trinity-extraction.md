# ZA v2.0.2 Trinity and ExeFS extraction

## Original file layout (observed in repository)

- ExeFS: v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/0/main, rtld and sdk.
- Native Trinity descriptor: .../1/arc/data.trpfd (9,877,520 bytes).
- Trinity container: .../1/arc/data.trpfs, stored as 87 ordered volumes from data.trpfs.7z.001 through .087, each up to 45 MiB.
- Source and volume size/SHA-256 are captured in manifests/v2.0.2/transfer_manifest.json. These manifest claims must be checked against local bytes before extraction.

The existing Archive-ZARomFS / Restore-ZARomFS code handles Git archival only; it does NOT extract the internal Trinity virtual filesystem. For that use the dedicated tools below. The new ZA dumper is **adapted from** the SV GFTool.Core parser: compatibility with ZA is a test hypothesis, not a verified extraction.

## One-time setup (Windows PowerShell)

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-ZA-Tools.ps1
$workspace = 'D:\ZA_Trinity_Workspace'  # outside ZA_Resources, with several GB free
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Prepare-ZA-Trinity.ps1 -Workspace $workspace
# If needed: -SevenZip '<absolute 7z.exe>' -OodleDllPath '<existing local Oodle DLL>'
~~~

Sync fetches pinned, real Git worktrees under ignored tools/_local. PokeDocs uses ZA/Hashlists/FileSystem, not SV. Prepare restores both trpfd and all trpfs volumes with the original-size/SHA-256 checks; generates the ZA-only GFPAKHashCache.bin; optionally adds ZA TRPAK hashes (-IncludeTrpakHashes). For previously restored inputs, -SkipRestore still performs SHA-256 verification. Oodle is local-only, not re-committed.

## Internal archive index and cautious extraction

~~~powershell
# Descriptor index only (no full TRPFS decode); requires descriptor, cache, GFTool.Core:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-ZA-TrinityDump.ps1 -Workspace $workspace -DescriptorOnly
# Trinity structure check only:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-ZA-TrinityDump.ps1 -Workspace $workspace -DryRun
# Bounded unpack:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-ZA-TrinityDump.ps1 -Workspace $workspace -MaxPacks 2 -MaxFiles 100
# All packs only after checking bounded outputs: MaxPacks 0 means no limit
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Run-ZA-TrinityDump.ps1 -Workspace $workspace -MaxPacks 0
~~~

Default outputs are under ignored Unpack/v2.0.2/romfs/arc/data.trpfs: virtual/ contains virtual paths (fallback _unknown/<hash>.bin); _index/ contains descriptor indexes and append-only export.jsonl containing hash, pack name/offset, extracted byte size, SHA-256 and failed entries. Unknown hashes are not assigned guessed names. Exit status may be nonzero for failed packs.

## Native NSO modules to ARM64 ELF

~~~powershell
cmake -S tools/_local/nx2elf -B .za-work/nx2elf-build -DCMAKE_BUILD_TYPE=Release
cmake --build .za-work/nx2elf-build --config Release
python .\scripts\Convert-ZA-ExeFS.py --nx2elf .\.za-work\nx2elf-build\Release\nx2elf.exe --names main
# Optionally also run --names rtld sdk after checking whether the converter accepts their module format.
~~~

The converter validates NSO0 build-id bytes, ELF64 little-endian AArch64 magic, output byte length and SHA-256. Generated ELF >= 90 MiB is archived as 90 MiB 7z volumes with a test and full hash round trip. Provenance is written alongside the output in Unpack/v2.0.2/exefs/<name>/provenance.json. Pass --keep-elf to retain the large raw file in ignored _work/ for local analysis. No decoded files are pushed automatically.

## Status and verification

- CONFIRMED: source paths, manifest and original archived representation exist in ZA_Resources.
- PENDING LOCAL CHECK: full archive restore, build of GFTool.Core and nx2elf, runtime decoder compatibility against ZA, decompression behavior, file-level extracted output hashes.
- CANDIDATE: names obtained solely from PokeDocs/ZA hash lists; do not infer type, item ID or game behavior from a path.
- UNKNOWN: full extractable count, correct virtual object types and any media/text conversion that requires separate parsers.

Synthetic tests: python -m unittest discover -s tests -p 'test_za_tooling.py' -v
