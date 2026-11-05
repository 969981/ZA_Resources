# ZA tools — complete pinned source snapshots

Six third-party tool projects are now available under tools/ as ordinary Git-tracked files. No gitlinks and no submodule initialization are required. The gftool/NxMiddleware nested dependency is present as actual source.

| Directory | Upstream | ZA role |
| --- | --- | --- |
| [gftool](gftool) | pkZukan/gftool | Trinity Core library, with nested NxMiddleware |
| [PokeDocs](PokeDocs) | pkZukan/PokeDocs | Complete multi-game hash lists and schemas, including ZA |
| [nx2elf](nx2elf) | shuffle2/nx2elf | NSO to AArch64 ELF |
| [pkNX](pkNX) | kwsch/pkNX | Cross-checking; ZA-specific support unproven |
| [Switch-Toolbox](Switch-Toolbox) | KillzXGaming/Switch-Toolbox | View supported image, model and archive formats |
| [SCVI_Extract](SCVI_Extract) | psthrn42/SCVI_Extract | Legacy Trinity cross-checks, ZA compatibility unproven |
| [HashCaches/ZA](HashCaches/ZA) | Derived from ZA file hash lists | Optional prebuilt GFPAKHashCache.bin |
| [PokeDocs-Supplement/ZA](PokeDocs-Supplement/ZA) | ZA analysis supplement | Lua hash recovery candidate evidence |
| [ZA.TrinityDump](ZA.TrinityDump) | ZA-specific project | GFTool.Core-based descriptor index and batch export |

The six full vendor trees and two ZA-only extra trees are pinned in [upstream.json](upstream.json). They were imported from [SV_Resources/tools](https://github.com/969981/SV_Resources/tree/master/tools) at commit 500f840087de687545d7ed3dbaee996d82335592. The imported trees contain no Git submodule pointers. Third-party licenses, bundled binaries, and distribution permissions must be considered before republishing.

## Build and verify (Windows)

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Sync-ZA-Tools.ps1 -VerifyOnly
dotnet build tools\ZA.TrinityDump\ZA.TrinityDump.csproj -c Release
cmake -S tools\nx2elf -B .za-work\nx2elf-build -DCMAKE_BUILD_TYPE=Release
cmake --build .za-work\nx2elf-build --config Release
~~~

Sync-ZA-Tools.ps1 now verifies committed source SHA trees; it does not clone from upstream. tools/_local is only for generated hash caches and local-only native runtime dependencies. ZA.TrinityDump references the committed tools/gftool/GFTool.Core project directly.

See [ZA unpack workflow](../docs/workflows/za-trinity-extraction.md). Cloning tool sources and compiling an extractor is not proof that all ZA game assets have been extracted successfully.
