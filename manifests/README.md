# Transfer manifests

Versioned manifests are produced only after running the local archive workflow. The v2.0.2 manifest path is `manifests/v2.0.2/transfer_manifest.json`.

Each entry records source-relative path, original size/SHA-256 and the stored artifact paths/sizes/SHA-256. Do not fabricate a manifest before source files are available. Do not store credentials or private host absolute paths.
