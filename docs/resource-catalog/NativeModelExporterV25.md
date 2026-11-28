# V2.5 Native Shader Core & Transparent Materials
[总览](README.md) · [V2.4](NativeModelExporterV24.md)
Baseline CI 46106057269 success, 15/21,30 GLBs,1657 mips. pm0006_52_00 UV1 displacement 316/366 vertices, max0.0821045578, normal/rare hash identical. Two remaining Charizard failed UV index: IntParameter schema default -1 and one-UV reference shader always UV0; preserve raw sentinel, correct effective UV only when NumRequiredUV=1, keep strict dual UV gate. 
## Independent Shader Core
TRSHA exact schema from PokeDocs SV render/trsha.fbs, source validated directly. Unlit 11 local/6 global options, EnableDisplacementMap mask0x100; FresnelEffect 10/2, FresnelTexture mask0x10; InsideEmissionParallax 24/10; Transparent11/5; IkCharacter29/6. Raw flags retained (IkCharacter flag5=2, not normalized bool). BNSH actual header GRSC offset0x60, count at GRSC+28, table at+32, 64-byte records with backpointer; program six stage descriptor pointers at+8. Unlit216 variations, FresnelEffect12. Two segment pointers/sizes as vendored Switch-Toolbox reference; hashes and bounds only, stage instruction meaning not proven. No assumption parameter buffer row maps directly to program index; preserve raw words. TRTCH technique param/shader/destination exact strings. SQLite normalized source,shader,shader_option,option_value,binary,variation,stage,technique,material_shader,error; exact-name links only, unknown aliases not guessed. CI may report unsupported BNSH variants, counts pending.
## Transparent candidate
Independent Zygarde material audit despite geometry rejection; preserve actual pass list, alpha_type, slot mappings, all TRMTR parameters. Single-pass Transparent/IkCharacterTransparent reference base+alpha path only, preserve alpha cutoff metadata; no multipass, Fresnel, SSS or InsideEmissionParallax substitution. Preview pixel hash only, no original PNG/GLB redistribution. No integration into strict full model export until native semantics are verified.
## Skin resolver result
V2.4 seven conflict shapes, no same-position+weight matches; eye raw9=head also valid palette-index9 mapping to rig16; direct only not proven. Other conflicts all direct valid/local invalid; names anatomically plausible, not proof. Keep gate unchanged.
## Reproduce
python scripts/ZANativeShaderCore.py
python scripts/Audit-ZATransparentMaterials.py
python scripts/ZANativeModelExporterV21.py
All metadata under .za-work, no original binary exports. No GPU decompilation, native visual parity or runtime variant mapping claim.
