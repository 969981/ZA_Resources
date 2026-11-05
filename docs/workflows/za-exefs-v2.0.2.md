# ZA v2.0.2 ExeFS: NSO, ELF and NPDM

## Input and scope

Original directory: v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/0, containing main, rtld, sdk and main.npdm. Preserve each original SHA-256 and original file; create derived artifacts only under Unpack/v2.0.2/exefs.

## Source-proven output layout

| Original | Export | Verified output bytes |
| --- | --- | ---: |
| main | main/main.elf | 66,579,944 |
| main | main/main.uncompressed.nso | 66,577,712 |
| rtld | rtld/rtld.elf | 17,792 |
| rtld | rtld/rtld.uncompressed.nso | 16,648 |
| sdk | sdk/sdk.elf | 12,120,392 |
| sdk | sdk/sdk.uncompressed.nso | 12,121,568 |
| main.npdm | main.npdm/ACID.bin, main.npdm/ACI0.bin, metadata.json, original copy | source 1,700 |

These byte counts were measured in the GitHub Actions extraction run. Each module has provenance.json with source SHA-256, BuildID, ELF SHA-256 and uncompressed NSO SHA-256. The consolidated exefs-manifest.json rehashes all derived artifacts.

## NPDM structure confirmed directly from source

- META starts at 0x0.
- ACID section envelope starts at 0x80, 0x3E4 bytes, with ACID magic at 0x280. The first 0x200 bytes contain signature and modulus material.
- ACI0 section begins at 0x470, 0x234 bytes, with ACI0 magic at its start.
- The two META-referenced sections are in bounds and do not overlap. This is structural byte evidence, not an interpretation of every permission field.

## Reproduce

~~~powershell
cmake -S tools/nx2elf -B .za-work/nx2elf-build -DCMAKE_BUILD_TYPE=Release
cmake --build .za-work/nx2elf-build --config Release
python scripts/Extract-ZA-NPDM.py
python scripts/Convert-ZA-ExeFS.py --nx2elf .za-work/nx2elf-build/Release/nx2elf.exe --names main rtld sdk --export-uncompressed
python scripts/Summarize-ZA-ExeFS.py
~~~

Executable path depends on CMake generator; Linux typically uses .za-work/nx2elf-build/nx2elf.

## Validation and publication

Workflow: [.github/workflows/za-exefs-unpack.yml](../../.github/workflows/za-exefs-unpack.yml). It performs a sparse checkout of ExeFS inputs and nx2elf sources; compiles nx2elf; validates ELF64 little endian AArch64 header, NSO input and output BuildID; hashes generated outputs and NPDM components; uploads a GitHub Actions artifact; commits explicitly validated derived files using git add --sparse -f.

Any output at least 90 MiB is stored in 90 MiB 7z volumes with round-trip SHA-256 verification. This run's individual outputs were below that threshold, so they are ordinary ELF/NSO files. The original NSO files remain compressed and unmodified in NCA/0.

ELF reconstruction is meant for reverse-engineering tools such as IDA and Ghidra; it is not itself a pre-populated IDA/Ghidra database. Function labels and game behavior require subsequent static and runtime evidence.
