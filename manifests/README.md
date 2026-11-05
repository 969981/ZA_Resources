# Transfer manifests

The v2.0.2 RomFS workflow writes the requested flat CSV to
manifests/v2.0.2-romfs-inventory.csv and detailed artifact metadata to
manifests/v2.0.2/transfer_manifest.json, with batch outcomes in
manifests/v2.0.2-git-batches.csv. The batch ledger distinguishes artifact-file count
from total files changed by the corresponding commit.

Each CSV row records source-relative path, original size and SHA-256,
representation, first target artifact path, volume count, total stored bytes,
verification status and Git batch. The JSON also records each part path, size
and SHA-256, compression settings and excluded temporary/cache entries. No
source-host absolute paths or credentials belong in a manifest.
