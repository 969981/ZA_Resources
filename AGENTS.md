# AGENTS.md — ZA_Resources

## Mission
Maintain a reproducible, evidence-based Pokémon Legends: Z-A research repository. Original ExeFS/RomFS bytes and original relative paths are immutable inputs. Distinguish observations from hypotheses.

## Repository invariants
1. Preserve all current files under `v2.0.2/4a70b3ff963bfe412681185cea68bf55_NCA/0/` and the existing `v2.0.2_file_inventory.csv` unchanged.
2. Game resources live in `<version>/<NCA_ID>_NCA/0` (ExeFS) and `.../1` (RomFS). Preserve every original basename and relative path.
3. Files larger than 90 MiB use 7-Zip volumes created with `-t7z -mx=1 -v90m`, stored alongside their corresponding original path as `<name>.7z.001`, `.002`, etc. No ordinary Git blob may reach 100,000,000 bytes.
4. A manifest must retain original byte length, SHA-256, archive-part paths, archive-part sizes and SHA-256. Validate with `7z t` and, for full verification, restore and compare original SHA-256.
5. Source directories are read-only inputs: never move, edit, rename or delete source data during import.
6. Documentation belongs under `docs/`; processing scripts under `scripts/`; synthetic tests under `tests/`; manifests under `manifests/<version>/`. Do not put temporary output in Git.
7. Never introduce ROM/title keys, secrets, credentials, unlicensed third-party assets, temporary installers or confidential local paths.
8. Stage explicit artifact paths. Separate documentation/code commits from bulk resource commits. Do not force-push, reset the branch, rewrite its history or overwrite a changed remote head.
9. Do not infer Pokémon species IDs, item IDs, archive offsets, language table joins or gameplay behavior from naming alone. Document evidence and use `CONFIRMED`, `CANDIDATE`, `UNKNOWN`, `REJECTED`.
10. Every new parser or archive workflow requires usage examples, reproducible validation and synthetic tests. Do not report an unrun test as passed.

## Before updating
Check repository state, branch HEAD and existing files. Read `README.md`, `docs/README.md`, `docs/repository-layout.md` and `docs/resource-provenance.md`. Prefer non-destructive additions. After editing, run the relevant tests, inspect changed paths and report commits and remaining limits.

## Rights and access
This archive may refer to copyrighted game material. Ensure you have the necessary rights and follow repository visibility/access controls; private hosting alone is not a redistribution license.
