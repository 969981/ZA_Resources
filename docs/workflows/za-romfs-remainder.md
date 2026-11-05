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

The two large Stream PCK packages first generate native extracted media as private Actions artifacts. The follow-up [PCK archive workflow](../../.github/workflows/za-pck-media-archive.yml) downloads the **already verified** extracted media from run 42055289781, checks every indexed WEM ID, path, original byte count and SHA-256, then packs each source directory using 7-Zip `-t7z -mx=1 -v90m`. Archive volumes and a source-to-volume SHA-256 manifest are committed under `Unpack/v2.0.2/romfs/audio/wwise/bin/Switch/_media_archives/`. Each Git commit/push contains at most 450 MiB of archive blobs, well below the requested 2 GiB push ceiling. Every archive receives both `7z t` and an independent full extraction/hash comparison before publishing. These Git volumes persist beyond the 14-day Actions artifact retention. Each PCK JSON index records absolute positions, IDs, sizes, SHA-256, language IDs and validation states. LooseMedia.pck may legitimately contain zero entries; a successfully parsed empty package is not an extraction failure.

Under Unpack/v2.0.2/romfs/system/config/data/, the TROWC source is copied byte-for-byte, printable NUL-terminated keys are listed with byte offsets in TSV, and a JSON report preserves source hash. Numerical config values and types remain UNKNOWN until their real native schema is established. The result must not be mislabeled as a decoded configuration.

Unpack/v2.0.2/romfs/_index/remaining-romfs-audit.json gives a status for every original file. COMPLETE for audio means structurally parsed, bounds checked and extracted; PARTIAL means unknown media magic or the still-opaque TROWC schema. This work does not modify the independent 13,181-pack Trinity M2 extraction.

A code commit or workflow trigger alone does not imply source extraction succeeded. Check the final workflow run, published audit, and package-media artifacts.

## Restoring the Git-resident PCK extracted media

Once the archive workflow publishes `media-archive-manifest.json` and every `.7z.00N` volume, enter the directory containing the volumes, and run:

    7z t Stream.pck.media.7z.001
    7z x Stream.pck.media.7z.001 -o<target-directory>
    7z t Stream_dlc.pck.media.7z.001
    7z x Stream_dlc.pck.media.7z.001 -o<target-directory>

The extracted directory tree will contain `Stream/stream/.../*.wem` and `Stream_dlc/stream/.../*.wem`, including any other catalogued media types. Cross-check their per-file hashes against the immutable `_index/Stream*.pck.json` catalogs; the committed `media-archive-manifest.json` includes each compressed volume's SHA-256, byte size, source run, and original package SHA-256.

The automatic archive job uses the original workflow's two private artifacts and does **not** reconstruct audio from the original PCKs again. Original containers remain untouched. The archive workflow is a separate, one-time publishing phase, not a requirement to rerun the 13,181-pack Trinity M2 job.
