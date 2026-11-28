---
title: ZA 2.0.2 道具原生图片路径与 UI ARC 组件审计
tags: [ZA, ARM64, SARC, BFLYT, BFLAN, UikitPokeIcon]
status: elf-static-audit-pass-archive-coverage-pending
---
# 图标选择器第七阶段
[[za-texture-binding]] · [[za-resource-key-scanner]] · [[za-icon-registration]]

## 验收范围
PR #9 draft. ELF SHA256 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d.
[Run 45772723593](https://github.com/969981/ZA_Resources/actions/runs/45772723593) elf job success, 7 branches, 9 windows; [Run 45772818194](https://github.com/969981/ZA_Resources/actions/runs/45772818194) elf job success, 37 branches, 13 windows. [Expanded ELF artifact](https://github.com/969981/ZA_Resources/actions/runs/45772818194/artifacts/15094502469). Both archive jobs still in checkout at last observation; no full archive parse success claimed.

## Raw UI inventory
Git tree 166fb2e30de06758b01bb39ee38605971726458c, non-truncated: 76 immediate directories, 980 raw .arc paths, 665 distinct Git blobs, 315 duplicate paths, 6,041,936,216 bytes by path, 4,467,554,440 bytes by distinct blob; no .arc.7z parts. Script scans unique blob once and retains all path aliases. Checkout still needed for actual member coverage. No files overwritten, no asset binaries exported to new commits.

## Item path chain (held-item UI)
0x2D32D0C..0x2D32D80:
- W0=W20, W1=4; BL 0x886240 at 0x2D32D18, indirect output local. Previous 0x88624C implementation uses printf-style nested integer format; exact wrapper 0x886240 not independently disassembled in this turn, so four-digit zero padding is a strongly supported candidate, not yet directly verified.
- 0x2D32D24 BL 0x2D335CC -> 0x2D33B50; prefix literal item_ at 0x32946DB, length 5.
- 0x2D32D3C BL 0x2D33624 with X0 and X1 both pointing to same item-name local; wrapper calls 0x2D33BE4 at 0x2D33660, then 0x7DEFC0 at 0x2D3366C.
- 0x2D33BE4..0x2D33CD8 forms ui/tex/icon_item/{name}/{name}.bntx (five pieces, 0x2A02B0 at 0x2D33CA4; main RET 0x2D33CB8 and null branches through 0x2D33CD8).
- 0x2D32D48 loads P_item_icon_00, 0x2D32D6C converts result to view, 0x2D32D80 BL 0x3D45CC with X0=UI context X19, X1=node view, X2=texture path view, W3=0.
- Nearby T_item_00 and msg_ui_status_pokemon_equip_01 support held-item status UI interpretation. Need trace W20 producer and item metadata, including exceptions and fallback. Do not claim every ItemID maps to a file.
Example hypothesis for 1785: ui/tex/icon_item/item_1785/item_1785.bntx (same literal previously verified); cannot infer every ID.

## HUD texture function
0x2D6AEA0 entry, primary RET 0x2D6B140, additional branches at 0x2D6B144/148/158/164 etc. Direct calls at 0x2C10974, 0x2C109B4, 0x2C109F4 all within 0x2C10918; caller keys 0x3DE7400=P_name_00, 0x3DE7418=P_name_01, 0x3DE7430=P_name_effect_00. Parent call at 0x2C11014.
0x9BB3F0/0x3D46B8 construct source string; 0x432CCC searches separator and constructs result vector candidate. Last element selected via end-8. 0x629D8C removes .bntx; 0x6D388 clamps start and count to source length and formats substring, caller supplies start 0/count length-2. Virtual slot +0x7D0 feeds 0x2D69E24 locale-name conversion candidate. 0x2D6B094 exact format ui/tex/hud_spmg/%s/hud_spmg_%s_00/hud_spmg_%s_00.bntx; args: X3 locale name, X4/X5 same processed name; 0x31607C0 at 0x2D6B0B4. 0xA7FE54 produces view, 0x3D45CC at 0x2D6B0DC consumes context/node/path/flag. Main return combines nonnull original object and bind result. This is HUD text/image localization-related path handling, not a Pokemon species selector.
## Shared bind candidate
0x3D45CC reads context+0xA8/+0xB0/+0xB8, calls 0xF65720, checks returned pointers, calls 0x10000C8 with node and flag, 0x2B50FC with resource path, continues. This is shared actual UI image request/bind candidate backed by two separate callers; texture GPU assignment or UikitPokeIcon exact class not proven.
## Direct archive sample
box/box_list_00.arc (Git blob 1c3703b3a570cc08c196e584e95d65d9a682e08c), 792908 bytes, SARC 39 members. blyt/box_box_button_00.bflyt P_icon_00 at 420,2564,3716; anim/box_box_button_00_search_target.bflan P_icon_00 at 132,204; switch_condition at 204; search_nontarget at 136,208. timg/__Combined.bntx 401536 bytes. No literal UikitPokeIcon in this sample. Member-name BNTX presence is distinct from bytes-level hit. Full scan pending.
## Scripts
scripts/Scan-ZA-UIArchives.py: strict SARC bounds, blob hash, member metadata, FLYT/FLAN section scan, ASCII token matches. Does not yet decode component registration schemas, layout material indices, nested compressed archives or pixels.
scripts/Probe-ZA-TextureProducers.py: bounded windows/direct branches/adjacent literal extraction; function boundaries inferred from prologues require corroboration.
Next: trace W20 and 0x886240 wrapper; trace 0x3D45CC downstream 0xF65720/0x10000C8/0x2B50FC; verify 980 archive paths parsed, then map layout pic1/mat1/txl1 and UikitPokeIcon component metadata. Runtime test not performed.
