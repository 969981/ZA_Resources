# ZA v2.0.2 — virtual to virtual_converted

## Source and destination

- Input: Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/
- Output: Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/
- Native source-of-truth: data.trpfs/_index/file_index.tsv.gz and data.trpfd/descriptor_summary.json.
- Do not modify original virtual files. Every original physical file receives a SHA-256 indexed result. The native index has 238,546 logical file records over 13,181 packs (including 25 unnamed hashes).

## Verified current implementation

| Suffix/input | Output | Status and proof |
|---|---|---|
| AHTB .tbl | .tbl.json hash/name entries | CONVERTED: validates AHTB magic, count, entry bounds, UTF-8 names and trailing bytes. Does not claim matching DAT text. |
| ik_message .dat | .dat.structure.json | STRUCTURE_ONLY: header/section data only, not the encrypted text string table. |
| selected Trinity FlatBuffer-compatible types (.trmdl, .trmsh, .trskl, .tranm, etc.) | .structure.json | STRUCTURE_ONLY: root table/vtable bounds only. NOT a mesh/texture/animation conversion. |
| JSON/XML/CSV/TSV/UTF-8 text | normalized text file | CONVERTED: validates the format where a standard parser is available; generic YAML is validated only as UTF-8 text. |
| GZip/ZIP | extracted bytes | EXTRACTED_ONLY: container extraction, not automatic nested semantic interpretation. |
| Unsupported formats (.bntx, .imap, .blua, .trpak, many .bin, etc.) | audit entry | UNSUPPORTED, never silently copied and renamed. |
| Any exception/integrity failure | audit entry with error | FAILED, exit nonzero. |

All original multipart 7z volume pieces remain accounted for. The .001 part is reconstructed by 7z, integrity-tested and passed to the format converter; subsequent pieces are labelled VOLUME_PART and verified with their own SHA-256. Converted files >=90 MiB are split with 7z -t7z -mx=1 -v90m and round-trip SHA-256 checked. No source is modified.

## Commands

Run from the repository root on a machine with Python 3.12 and 7-Zip installed:

~~~bash
python -m unittest discover -s tests -p test_za_virtual_convert.py -v
python scripts/Convert-ZA-Virtual.py --repo . --category ik_message --workers 4 --seven-zip 7z
python scripts/Convert-ZA-Virtual.py --repo . --category ik_pokemon --workers 4 --seven-zip 7z --publish
python scripts/Audit-ZA-VirtualConversion.py --repo .
~~~

CI: .github/workflows/za-virtual-convert.yml supports manual dispatch, an initial push pass and an automatic final pass when the native ZA M2 full extraction workflow completes successfully. It processes real source subdirectories with three concurrent category jobs and commits output via the existing non-force, remote-head-aware publisher. Check workflow logs for checkout disk limitations or GitHub API upload failures.

## Audits

- Per-category: virtual_converted/_index/<category>.jsonl.gz and <category>.summary.json.
- Global: virtual_converted/_index/native-coverage-audit.json.
- Each original: sourcePath, sourceBytes, sourceSha256, parser version, status, output paths, bytes, SHA-256 and error/proof note.
- Global audit compares logical paths against all 238,546 original TRPFD rows, including _unknown/<hash>.bin and reconstructed multipart filenames.
- A PARTIAL native source checkpoint cannot yield semanticConversionComplete. Neither STRUCTURE_ONLY nor EXTRACTED_ONLY count as full semantic decoding.
- File coverage and semantic decoding are separate metrics. The global audit intentionally fails full-completion enforcement if any unsupported parser, unconverted file, missing path, archive failure or source extraction gap remains.

## Next native format adapters

Implement and validate content exporters for Switch BNTX textures to PNG/DDS; model mesh/material/skeleton/animation to glTF; text DAT encrypted strings and trusted AHTB joining; Lua bytecode decompilation; and game-specific IMAP/scene/event files. GFTool and Switch-Toolbox are available as source references but are not proven automated CLI converters for all ZA 2.0.2 formats. A viewer loading a file or a FlatBuffer vtable check is not proof of a complete export.

Only upgrade a result from STRUCTURE_ONLY or UNSUPPORTED to CONVERTED after independently verified semantics and an output round-trip / source comparison appropriate to that format.
