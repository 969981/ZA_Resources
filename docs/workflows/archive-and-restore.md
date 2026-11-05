# ZA M1: local RomFS archive, verify and restore

The source game files are on the operator's Windows disk; scripts cannot read them from GitHub. This workflow makes a **separate copy** into a local ZA_Resources clone. It does not upload anything automatically.

## 1. Prepare

Requirements: PowerShell 5.1+ or PowerShell 7, 7-Zip, a Git clone and enough free space for temporary 7z volumes and a restored verification copy. Large archives are deliberately tested against source SHA-256. Local source paths must not coincide with the destination repository `.../1/` directory.

If Windows blocks unsigned scripts, use `Set-ExecutionPolicy -Scope Process Bypass -Force` in the **current** PowerShell terminal. This does not permanently alter the machine policy. Run only code you have reviewed.

```powershell
git clone https://github.com/969981/ZA_Resources.git D:\Repos\ZA_Resources
cd D:\Repos\ZA_Resources
Set-ExecutionPolicy -Scope Process Bypass -Force

$source = 'X:\ROMS\Nintendo Switch\Pokemon\Pokemon Legends ZA\v2.0.2\4a70b3ff963bfe412681185cea68bf55_NCA\1'
.\scripts\Archive-ZAResources.ps1 -SourceRomfsRoot $source -SevenZip 'D:\Tool\7-Zip\7z.exe'
```

Default threshold is 90 MiB (94,371,840 bytes). Original files **larger** than that are archived with 7z `-t7z -mx=1 -v90m`, yielding `<name>.7z.001`, `.002` and so forth; smaller files are copied without conversion. Each archive stores just the original file name, and its volumes remain in the same parent path inside the version/NCA/RomFS tree. An archive is tested and fully reconstructed for original SHA-256 verification before adding it to the manifest. Existing destination bytes are compared and never silently overwritten.

For a different game version, pass `-Version vX.Y.Z` and its corresponding `-NcaDirectory <hex>_NCA`. For synthetic testing, reduce threshold and volume with `-ThresholdMiB 1 -VolumeMiB 1`.

## 2. Validate

```powershell
.\scripts\Verify-ZAArchives.ps1 -SevenZip 'D:\Tool\7-Zip\7z.exe'
.\scripts\Verify-ZAArchives.ps1 -SevenZip 'D:\Tool\7-Zip\7z.exe' -Full
```

Normal verification checks each artifact's byte size and SHA-256, each copied original's SHA-256, and `7z t` for every archive. `-Full` reconstructs **all** files into a temporary ignored work area and compares each to the manifest's original SHA-256. Allow sufficient scratch space (several GB for v2.0.2). Temporary full-verification output is deleted afterward.

## 3. Restore to a separate directory

```powershell
.\scripts\Restore-ZAResources.ps1 -DestinationRoot 'D:\ZA_Restored' -SevenZip 'D:\Tool\7-Zip\7z.exe'
```

Restored files appear under `D:\ZA_Restored\arc`, `audio` and `system`, with the original RomFS hierarchy intact. Restore never overwrites an existing file whose SHA-256 does not match the manifest.

## 4. Review and commit in batches (manual)

Inspect `git status --short` and `manifests/v2.0.2/transfer_manifest.json` first. Stage explicit paths and keep commits of large resources to about 500–600 MiB rather than doing `git add .` or `git add -A`. After every batch, push normally; stop if the remote head changed. Commit the manifest **after** all its referenced artifacts have been pushed to keep the remote repository reconstructable.

Example:

```powershell
git status --short
git add -- 'v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/arc/data.trpfd'
git commit -m 'data: add ZA 2.0.2 Trinity descriptor'
git push origin master
```

For a split file, explicitly stage a limited range of `.7z.001`, `.002` etc. with each commit; finish the file before uploading the manifest. The scripts **do not** stage, commit, push or delete files.

## Safety and constraints

The GitHub ordinary Git hard limit is 100 MB per object; 90 MiB volumes fit it but a many-gigabyte repository can still be impractical. Consider authorized private artifact/object storage for bulk raw resources. The repository being private does not itself grant redistribution permission.

An interrupted run may leave part of a volume set. The archiver refuses incomplete/non-contiguous sets instead of overwriting them; inspect and manually clear only verified incomplete output before restarting. `.za-work/` and `.za-restore/` are ignored staging folders, never original inputs.
