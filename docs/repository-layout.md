# Layout and naming policy

v2.0.2/<NCA_ID>_NCA/0/ contains the original ExeFS files. Keep those files and the existing v2.0.2 file inventory unchanged.

v2.0.2/<NCA_ID>_NCA/1/ mirrors the original RomFS paths. For the v2.0.2 RomFS archive defined in [the task workflow](romfs-v2.0.2-archive.md), files smaller than 20 MiB remain raw and files at least 20 MiB are represented by <originalname>.7z.001, .002, and later parts in the same parent directory. The archive contains only the original basename, not a host absolute path.

manifests/v2.0.2-romfs-inventory.csv records the requested inventory fields. manifests/v2.0.2/transfer_manifest.json records each stored artifact path, byte length and SHA-256. docs/ contains documentation, scripts/ maintained tools, and tests/ synthetic fixtures. Local .za-work and .za-restore outputs are excluded from Git.

Version upgrades create a new vX.Y.Z/<NCA_ID>_NCA/ tree rather than replacing previous version bytes. Preserve case and spelling, including the NCA folder ID. Ordinary Git blobs must remain below GitHub's 100,000,000 byte file limit.
