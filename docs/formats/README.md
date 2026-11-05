# Resource formats — ZA

- `0/main`, `rtld` and `sdk`: ExeFS executable modules; NSO headers and build IDs require binary validation.
- `0/main.npdm`: Nintendo program metadata.
- `1/arc/data.trpfd`: Trinity file/pack descriptor data — detailed field layout is **UNKNOWN** until decoded from original bytes.
- `1/arc/data.trpfs`: Trinity resource container — restore original bytes before attempting an internal extraction.
- `1/audio/wwise/bin/Switch/*.bnk` and `*.pck`: Wwise bank and packaged media files. Names alone are not proof of contained events.
- `1/system/config/data/trinity_config.trowc`: Trinity configuration file; schema not yet verified.

Record actual signatures, offset/length checks, hashes and sample commands in `docs/research/v2.0.2/` before assigning semantics to data fields.
