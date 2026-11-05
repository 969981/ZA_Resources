# ZA v2.0.2 — remaining RomFS extraction

## Inventory

The original inventory has exactly 20 non-Trinity sources: 16 Wwise BNK soundbanks, 3 Wwise PCK packages under audio/wwise/bin/Switch/, and one system/config/data/trinity_config.trowc. Preserve original files under v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/1/. Source byte sizes, SHA-256 hashes and seven-zip volumes are documented in manifests/v2.0.2/transfer_manifest.json.

## Reproducible extraction

Run the GitHub Actions workflow at .github/workflows/za-romfs-remainder.yml. It restores all 20 files with the repository's existing Restore-ZARomFS.ps1 checks, then invokes the checked Python parser with the recovered source root, output root Unpack/v2.0.2/romfs and separate large-package media output root. Run the synthetic checks with:

    python -m unittest discover -s tests -p test_za_romfs_remainder.py -v

Manual parser invocation after restoring source files:

    python scripts/Extract-ZA-RomFS-Remainder.py --source-root .za-restored --output-root Unpack/v2.0.2/romfs --pck-media-root .za-media --manifest manifests/v2.0.2/transfer_manifest.json

## Produced data and evidence levels

Under Unpack/v2.0.2/romfs/audio/wwise/bin/Switch/, the _index directory holds JSON for each BNK/PCK, and _embedded contains the original encoded media referenced by BNK DIDX sections. HIRC object IDs and types are retained without inventing human-readable names. If the extracted payload is not a recognized RIFF/RIFX WEM, it is emitted as BIN and marked UNKNOWN_MAGIC.

The two large Stream PCK packages generate native media in private Actions artifacts rather than pushing another ~1 GB of copyrighted audio data into Git history. Each PCK JSON index records absolute positions, IDs, sizes, SHA-256, language IDs and validation states. LooseMedia.pck may legitimately contain zero entries; a successfully parsed empty package is not an extraction failure.

Under Unpack/v2.0.2/romfs/system/config/data/, the TROWC source is copied byte-for-byte, printable NUL-terminated keys are listed with byte offsets in TSV, and a JSON report preserves source hash. Numerical config values and types remain UNKNOWN until their real native schema is established. The result must not be mislabeled as a decoded configuration.

Unpack/v2.0.2/romfs/_index/remaining-romfs-audit.json gives a status for every original file. COMPLETE for audio means structurally parsed, bounds checked and extracted; PARTIAL means unknown media magic or the still-opaque TROWC schema. This work does not modify the independent 13,181-pack Trinity M2 extraction.

A code commit or workflow trigger alone does not imply source extraction succeeded. Check the final workflow run, published audit, and package-media artifacts.