# ZA tools — pinned source dependencies

Mirrors the roles of [SV_Resources/tools](https://github.com/969981/SV_Resources/tree/master/tools), but uses ZA-specific hashes and original NCA paths. See [upstream.json](upstream.json) for URLs and pinned commits.

- P0 gftool (Trinity TRPFD/TRPFS), PokeDocs (ZA/FileSystem Hashlists), nx2elf (NSO → ELF).
- P1 optional pkNX and Switch-Toolbox; P2 optional SCVI_Extract. Compatibility with ZA is NOT established for the optional reference tools.
- All upstream repositories are **real Git working trees in the ignored tools/_local folder**, not submodules/gitlinks, and not re-vendored into the massive ZA Git history. Pinned checkout requires a one-time local download.
- Maintained ZA-specific source is in [ZA.TrinityDump](ZA.TrinityDump/). The GFTool.Core project reference points to ../_local/gftool/GFTool.Core/GFTool.Core.csproj.
- The existing scripts/deps/Oodle library is not imported or redistributed again. Respect upstream licenses.

### Windows bootstrap

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-ZA-Tools.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-ZA-Tools.ps1 -VerifyOnly
# Optional large reference checkouts:
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-ZA-Tools.ps1 -IncludeOptional
cmake -S tools/_local/nx2elf -B .za-work/nx2elf-build -DCMAKE_BUILD_TYPE=Release
cmake --build .za-work/nx2elf-build --config Release
~~~

Then use [the ZA unpack instructions](../docs/workflows/za-trinity-extraction.md). Tool installation alone does not demonstrate a successful ZA data extraction.
