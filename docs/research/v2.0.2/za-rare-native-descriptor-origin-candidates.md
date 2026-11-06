# Z-A v2.0.2 Potential origin/copy functions before native Rare +0x68 exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 4
- Instruction window: 0x10 bytes before and 0x460 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0xBEF804 (word native_entry_candidate)

- ELF file offset: VA-to-ELF-segment-mapped; opcode: STATIC_FUNCTION_WINDOW; mask: pre_generator_data_builder
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xBEF7F4: ldp      x28, x19, [sp, #0x110] ; fc4f51a9
   0xBEF7F8: ldp      x29, x30, [sp, #0x100] ; fd7b50a9
   0xBEF7FC: add      sp, sp, #0x120 ; ff830491
   0xBEF800: ret       ; c0035fd6
>> 0xBEF804: mov      w2, #0xf8 ; 021f8052
   0xBEF808: stur     xzr, [x0, #0xd2] ; 1f200df8
   0xBEF80C: stur     xzr, [x0, #0xca] ; 1fa00cf8
   0xBEF810: stur     xzr, [x0, #0xc2] ; 1f200cf8
   0xBEF814: stur     xzr, [x0, #0xba] ; 1fa00bf8
   0xBEF818: stur     xzr, [x0, #0xb2] ; 1f200bf8
   0xBEF81C: stur     xzr, [x0, #0xaa] ; 1fa00af8
   0xBEF820: stur     xzr, [x0, #0xa2] ; 1f200af8
   0xBEF824: b        #0x3161510 ; 3bc79514
   0xBEF828: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0xBEF82C: str      x19, [sp, #0x10] ; f30b00f9
   0xBEF830: mov      x29, sp ; fd030091
   0xBEF834: mov      x19, x8 ; f30308aa
   0xBEF838: adrp     x8, #0x610b000 ; e8a80290
   0xBEF83C: add      x8, x8, #0x200 ; 08010891
   0xBEF840: mov      x1, x0 ; e10300aa
   0xBEF844: ldr      x0, [x8, #8] ; 000540f9
   0xBEF848: add      x8, x29, #0x18 ; a8630091
   0xBEF84C: bl       #0x656ca4 ; 169de997
   0xBEF850: ldr      x8, [x29, #0x18] ; a80f40f9
   0xBEF854: add      x0, x29, #0x18 ; a0630091
   0xBEF858: str      xzr, [x29, #0x18] ; bf0f00f9
   0xBEF85C: str      x8, [x19] ; 680200f9
   0xBEF860: bl       #0xa0d050 ; fc75f897
   0xBEF864: ldr      x19, [sp, #0x10] ; f30b40f9
   0xBEF868: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0xBEF86C: ret       ; c0035fd6
   0xBEF870: ldrb     w8, [x0] ; 08004039
   0xBEF874: cmp      w8, #1 ; 1f050071
   0xBEF878: ldr      x0, [x0, #8] ; 000440f9
   0xBEF87C: ccmp     x0, #0, #4, ls ; 049840fa
   0xBEF880: b.eq     #0xbef888 ; 40000054
   0xBEF884: ret       ; c0035fd6
   0xBEF888: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0xBEF88C: str      x19, [sp, #0x10] ; f30b00f9
   0xBEF890: mov      x29, sp ; fd030091
   0xBEF894: adrp     x8, #0x6121000 ; 88a902d0
   0xBEF898: add      x8, x8, #0xea0 ; 08813a91
   0xBEF89C: ldarb    w8, [x8] ; 08fddf08
   0xBEF8A0: tbz      w8, #0, #0xbef8b8 ; c8000036
   0xBEF8A4: adrp     x0, #0x6121000 ; 80a902d0
   0xBEF8A8: add      x0, x0, #0xda8 ; 00a03691
   0xBEF8AC: ldr      x19, [sp, #0x10] ; f30b40f9
   0xBEF8B0: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0xBEF8B4: b        #0xbef884 ; f4ffff17
   0xBEF8B8: adrp     x0, #0x6121000 ; 80a902d0
   0xBEF8BC: add      x0, x0, #0xea0 ; 00803a91
   0xBEF8C0: bl       #0x3160620 ; 58c39594
   0xBEF8C4: cbz      w0, #0xbef8a4 ; 00ffff34
   0xBEF8C8: adrp     x19, #0x6121000 ; 93a902d0
   0xBEF8CC: add      x19, x19, #0xda8 ; 73a23691
   0xBEF8D0: mov      x0, x19 ; e00313aa
   0xBEF8D4: bl       #0xc8369c ; 724f0294
   0xBEF8D8: adrp     x0, #0x6121000 ; 80a902d0
   0xBEF8DC: add      x0, x0, #0xea0 ; 00803a91
   0xBEF8E0: bl       #0x3160630 ; 54c39594
   0xBEF8E4: mov      x0, x19 ; e00313aa
   0xBEF8E8: b        #0xbef8ac ; f1ffff17
   0xBEF8EC: sub      sp, sp, #0x80 ; ff0302d1
   0xBEF8F0: stp      x29, x30, [sp, #0x20] ; fd7b02a9
   0xBEF8F4: str      x27, [sp, #0x30] ; fb1b00f9
   0xBEF8F8: stp      x26, x25, [sp, #0x40] ; fa6704a9
   0xBEF8FC: stp      x24, x23, [sp, #0x50] ; f85f05a9
   0xBEF900: stp      x22, x21, [sp, #0x60] ; f65706a9
   0xBEF904: stp      x20, x19, [sp, #0x70] ; f44f07a9
   0xBEF908: add      x29, sp, #0x20 ; fd830091
   0xBEF90C: mov      x19, x0 ; f30300aa
   0xBEF910: tbz      w1, #0, #0xbefa48 ; c1090036
   0xBEF914: add      x20, x19, #0x100 ; 74020491
   0xBEF918: mov      x0, x20 ; e00314aa
   0xBEF91C: bl       #0xbefa70 ; 55000094
   0xBEF920: add      x0, x19, #0x40 ; 60020191
   0xBEF924: bl       #0x631710 ; 7b07e997
   0xBEF928: ldr      w8, [x0] ; 080040b9
   0xBEF92C: add      x10, x0, x8 ; 0a00088b
   0xBEF930: ldrsw    x9, [x10] ; 490180b9
   0xBEF934: sub      x9, x10, x9 ; 490109cb
   0xBEF938: ldrh     w11, [x9] ; 2b014079
   0xBEF93C: cmp      w11, #5 ; 7f150071
   0xBEF940: b.lo     #0xbefa28 ; 43070054
   0xBEF944: ldrh     w9, [x9, #4] ; 29094079
   0xBEF948: cbz      x9, #0xbefa28 ; 090700b4
   0xBEF94C: add      x11, x10, x9 ; 4b01098b
   0xBEF950: ldr      w10, [x11] ; 6a0140b9
   0xBEF954: add      x21, x11, x10 ; 75010a8b
   0xBEF958: ldr      w11, [x21], #4 ; ab4640b8
   0xBEF95C: cbz      w11, #0xbefa1c ; 0b060034
   0xBEF960: add      x9, x10, x9 ; 4901098b
   0xBEF964: add      x8, x8, x0 ; 0801008b
   0xBEF968: add      x22, x21, x11, lsl #2 ; b60a0b8b
   0xBEF96C: add      x8, x9, x8 ; 2801088b
   0xBEF970: mov      w23, #0x9dc5 ; b7b89352
   0xBEF974: movk     w23, #0x811c, lsl #16 ; 9723b072
   0xBEF978: add      x24, x8, #9 ; 18250091
   0xBEF97C: add      x25, sp, #0xc ; f9330091
   0xBEF980: add      x26, sp, #0x10 ; fa430091
   0xBEF984: mov      w27, #0x193 ; 7b328052
   0xBEF988: movk     w27, #0x100, lsl #16 ; 1b20a072
   0xBEF98C: ldr      w8, [x21] ; a80240b9
   0xBEF990: add      x9, x21, x8 ; a902088b
   0xBEF994: str      x9, [sp, #0x10] ; e90b00f9
   0xBEF998: ldrsw    x10, [x9] ; 2a0180b9
   0xBEF99C: sub      x10, x9, x10 ; 2a010acb
   0xBEF9A0: ldrh     w11, [x10] ; 4b014079
   0xBEF9A4: cmp      w11, #5 ; 7f150071
   0xBEF9A8: b.lo     #0xbefa28 ; 03040054
   0xBEF9AC: ldrh     w11, [x10, #4] ; 4b094079
   0xBEF9B0: cbz      x11, #0xbefa28 ; cb0300b4
   0xBEF9B4: add      x9, x9, x11 ; 29010b8b
   0xBEF9B8: mov      w10, w23 ; ea03172a
   0xBEF9BC: ldr      w12, [x9] ; 2c0140b9
   0xBEF9C0: add      x9, x9, x12 ; 29010c8b
   0xBEF9C4: ldrb     w9, [x9, #4] ; 29114039
   0xBEF9C8: cbz      w9, #0xbef9ec ; 29010034
   0xBEF9CC: add      x10, x12, x11 ; 8a010b8b
   0xBEF9D0: add      x8, x24, x8 ; 0803088b
   0xBEF9D4: add      x8, x8, x10 ; 08010a8b
   0xBEF9D8: mov      w10, w23 ; ea03172a
   0xBEF9DC: eor      w9, w10, w9 ; 4901094a
   0xBEF9E0: mul      w10, w9, w27 ; 2a7d1b1b
   0xBEF9E4: ldrb     w9, [x8], #1 ; 09154038
   0xBEF9E8: cbnz     w9, #0xbef9dc ; a9ffff35
   0xBEF9EC: add      x1, sp, #0xc ; e1330091
   0xBEF9F0: add      x2, x29, #0x18 ; a2630091
   0xBEF9F4: str      w10, [sp, #0xc] ; ea0f00b9
   0xBEF9F8: sub      x3, x29, #8 ; a32300d1
   0xBEF9FC: mov      x0, x20 ; e00314aa
   0xBEFA00: str      x25, [x29, #0x18] ; b90f00f9
   0xBEFA04: stur     x26, [x29, #-8] ; ba831ff8
   0xBEFA08: bl       #0xbefae4 ; 37000094
   0xBEFA0C: add      x21, x21, #4 ; b5120091
   0xBEFA10: add      x24, x24, #4 ; 18130091
   0xBEFA14: cmp      x21, x22 ; bf0216eb
   0xBEFA18: b.ne     #0xbef98c ; a1fbff54
   0xBEFA1C: mov      x0, x19 ; e00313aa
   0xBEFA20: mov      w1, #1 ; 21008052
   0xBEFA24: bl       #0x6722a4 ; 200aea97
   0xBEFA28: ldp      x20, x19, [sp, #0x70] ; f44f47a9
   0xBEFA2C: ldr      x27, [sp, #0x30] ; fb1b40f9
   0xBEFA30: ldp      x22, x21, [sp, #0x60] ; f65746a9
   0xBEFA34: ldp      x24, x23, [sp, #0x50] ; f85f45a9
   0xBEFA38: ldp      x26, x25, [sp, #0x40] ; fa6744a9
   0xBEFA3C: ldp      x29, x30, [sp, #0x20] ; fd7b42a9
   0xBEFA40: add      sp, sp, #0x80 ; ff030291
   0xBEFA44: ret       ; c0035fd6
   0xBEFA48: mov      x0, x19 ; e00313aa
   0xBEFA4C: ldp      x20, x19, [sp, #0x70] ; f44f47a9
   0xBEFA50: ldp      x22, x21, [sp, #0x60] ; f65746a9
   0xBEFA54: mov      w1, wzr ; e1031f2a
   0xBEFA58: ldp      x24, x23, [sp, #0x50] ; f85f45a9
   0xBEFA5C: ldr      x27, [sp, #0x30] ; fb1b40f9
   0xBEFA60: ldp      x26, x25, [sp, #0x40] ; fa6744a9
   0xBEFA64: ldp      x29, x30, [sp, #0x20] ; fd7b42a9
   0xBEFA68: add      sp, sp, #0x80 ; ff030291
   0xBEFA6C: b        #0x6722a4 ; 0e0aea17
   0xBEFA70: ldr      x8, [x0, #0x28] ; 081440f9
   0xBEFA74: cbnz     x8, #0xbefa7c ; 480000b5
   0xBEFA78: ret       ; c0035fd6
   0xBEFA7C: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0xBEFA80: stp      x20, x19, [sp, #0x10] ; f44f01a9
   0xBEFA84: mov      x29, sp ; fd030091
   0xBEFA88: ldr      x1, [x0, #0x18] ; 010c40f9
   0xBEFA8C: mov      x19, x0 ; f30300aa
   0xBEFA90: cbz      x1, #0xbefab0 ; 010100b4
   0xBEFA94: ldr      x0, [x19, #0x20] ; 601240f9
   0xBEFA98: mov      w2, #0x20 ; 02048052
   0xBEFA9C: mov      w3, #8 ; 03018052
   0xBEFAA0: ldr      x20, [x1] ; 340040f9
   0xBEFAA4: bl       #0xf308 ; 197ed097
   0xBEFAA8: mov      x1, x20 ; e10314aa
   0xBEFAAC: cbnz     x20, #0xbefa94 ; 54ffffb5
   0xBEFAB0: ldr      x8, [x19, #8] ; 680640f9
   0xBEFAB4: str      xzr, [x19, #0x18] ; 7f0e00f9
   0xBEFAB8: cbz      x8, #0xbefad4 ; e80000b4
   0xBEFABC: mov      x9, xzr ; e9031faa
   0xBEFAC0: ldr      x10, [x19] ; 6a0240f9
   0xBEFAC4: str      xzr, [x10, x9, lsl #3] ; 5f7929f8
   0xBEFAC8: add      x9, x9, #1 ; 29050091
   0xBEFACC: cmp      x8, x9 ; 1f0109eb
   0xBEFAD0: b.ne     #0xbefac0 ; 81ffff54
   0xBEFAD4: str      xzr, [x19, #0x28] ; 7f1600f9
   0xBEFAD8: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0xBEFADC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0xBEFAE0: b        #0xbefa78 ; e6ffff17
   0xBEFAE4: sub      sp, sp, #0x60 ; ff8301d1
   0xBEFAE8: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0xBEFAEC: str      x25, [sp, #0x20] ; f91300f9
   0xBEFAF0: stp      x24, x23, [sp, #0x30] ; f85f03a9
   0xBEFAF4: stp      x22, x21, [sp, #0x40] ; f65704a9
   0xBEFAF8: stp      x20, x19, [sp, #0x50] ; f44f05a9
   0xBEFAFC: add      x29, sp, #0x10 ; fd430091
   0xBEFB00: ldr      w23, [x1] ; 370040b9
   0xBEFB04: mov      x21, x3 ; f50303aa
   0xBEFB08: mov      x22, x2 ; f60302aa
   0xBEFB0C: ldr      x24, [x0, #8] ; 180440f9
   0xBEFB10: mov      x19, x0 ; f30300aa
   0xBEFB14: cbz      x24, #0xbefe3c ; 581900b4
   0xBEFB18: fmov     d0, x24 ; 0003679e
   0xBEFB1C: cnt      v0.8b, v0.8b ; 0058200e
   0xBEFB20: uaddlv   h0, v0.8b ; 0038302e
   0xBEFB24: fmov     w9, s0 ; 0900261e
   0xBEFB28: cmp      x9, #1 ; 3f0500f1
   0xBEFB2C: b.ls     #0xbefc8c ; 090b0054
   0xBEFB30: cmp      x24, x23 ; 1f0317eb
   0xBEFB34: mov      x25, x23 ; f90317aa
   0xBEFB38: b.hi     #0xbefb44 ; 68000054
   0xBEFB3C: udiv     x8, x23, x24 ; e80ad89a
   0xBEFB40: msub     x25, x8, x24, x23 ; 19dd189b
   0xBEFB44: ldr      x8, [x19] ; 680240f9
   0xBEFB48: ldr      x8, [x8, x25, lsl #3] ; 087979f8
   0xBEFB4C: cbnz     x8, #0xbefc40 ; a80700b5
   0xBEFB50: ldr      x0, [x19, #0x20] ; 601240f9
   0xBEFB54: mov      w1, #0x20 ; 01048052
   0xBEFB58: mov      w2, #8 ; 02018052
   0xBEFB5C: bl       #0x5388 ; 0b56d097
   0xBEFB60: mov      x20, x0 ; f40300aa
   0xBEFB64: ldr      x0, [x19, #0x20] ; 601240f9
   0xBEFB68: mov      x8, sp ; e8030091
   0xBEFB6C: bl       #0xbad0 ; d96fd097
   0xBEFB70: ldr      x8, [x22] ; c80240f9
   0xBEFB74: ldr      x9, [x21] ; a90240f9
   0xBEFB78: ldr      w8, [x8] ; 080140b9
   0xBEFB7C: str      w8, [x20, #0x10] ; 881200b9
   0xBEFB80: ldr      x8, [x9] ; 280140f9
   0xBEFB84: str      x8, [x20, #0x18] ; 880e00f9
   0xBEFB88: ldr      x8, [sp, #8] ; e80740f9
   0xBEFB8C: cbz      x8, #0xbefb98 ; 680000b4
   0xBEFB90: ldr      x0, [sp] ; e00340f9
   0xBEFB94: blr      x8 ; 00013fd6
   0xBEFB98: stp      xzr, x23, [x20] ; 9f5e00a9
   0xBEFB9C: ldr      x8, [x19, #0x28] ; 681640f9
   0xBEFBA0: ldr      s1, [x19, #0x30] ; 613240bd
   0xBEFBA4: add      x8, x8, #1 ; 08050091
   0xBEFBA8: ucvtf    s0, x8 ; 0001239e
   0xBEFBAC: cbz      x24, #0xbefc98 ; 780700b4
   0xBEFBB0: ucvtf    s2, x24 ; 0203239e
   0xBEFBB4: fmul     s2, s1, s2 ; 2208221e
   0xBEFBB8: fcmp     s2, s0 ; 4020201e
   0xBEFBBC: b.mi     #0xbefc98 ; e4060054
   0xBEFBC0: ldr      x8, [x19] ; 680240f9
   0xBEFBC4: ldr      x8, [x8, x25, lsl #3] ; 087979f8
   0xBEFBC8: cbnz     x8, #0xbefc80 ; c80500b5
   0xBEFBCC: mov      x8, x19 ; e80313aa
   0xBEFBD0: ldr      x9, [x8, #0x18]! ; 098d41f8
   0xBEFBD4: str      x9, [x20] ; 890200f9
   0xBEFBD8: str      x20, [x8] ; 140100f9
   0xBEFBDC: ldr      x9, [x19] ; 690240f9
   0xBEFBE0: str      x8, [x9, x25, lsl #3] ; 287939f8
   0xBEFBE4: ldr      x8, [x20] ; 880240f9
   0xBEFBE8: cbz      x8, #0xbefc18 ; 880100b4
   0xBEFBEC: ldr      x8, [x8, #8] ; 080540f9
   0xBEFBF0: sub      x9, x24, #1 ; 090700d1
   0xBEFBF4: tst      x24, x9 ; 1f0309ea
   0xBEFBF8: b.eq     #0xbefdfc ; 20100054
   0xBEFBFC: cmp      x8, x24 ; 1f0118eb
   0xBEFC00: b.lo     #0xbefc0c ; 63000054
   0xBEFC04: udiv     x9, x8, x24 ; 0909d89a
   0xBEFC08: msub     x8, x9, x24, x8 ; 28a1189b
   0xBEFC0C: ldr      x9, [x19] ; 690240f9
   0xBEFC10: add      x8, x9, x8, lsl #3 ; 280d088b
   0xBEFC14: str      x20, [x8] ; 140100f9
   0xBEFC18: ldr      x8, [x19, #0x28] ; 681640f9
   0xBEFC1C: add      x8, x8, #1 ; 08050091
   0xBEFC20: str      x8, [x19, #0x28] ; 681600f9
   0xBEFC24: ldp      x20, x19, [sp, #0x50] ; f44f45a9
   0xBEFC28: ldr      x25, [sp, #0x20] ; f91340f9
   0xBEFC2C: ldp      x22, x21, [sp, #0x40] ; f65744a9
   0xBEFC30: ldp      x24, x23, [sp, #0x30] ; f85f43a9
   0xBEFC34: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0xBEFC38: add      sp, sp, #0x60 ; ff830191
   0xBEFC3C: ret       ; c0035fd6
   0xBEFC40: ldr      x8, [x8] ; 080140f9
   0xBEFC44: cbz      x8, #0xbefb50 ; 68f8ffb4
   0xBEFC48: cmp      x9, #2 ; 3f0900f1
   0xBEFC4C: b.lo     #0xbefe04 ; c30d0054
   0xBEFC50: ldr      x9, [x8, #8] ; 090540f9
   0xBEFC54: cmp      x9, x23 ; 3f0117eb
   0xBEFC58: b.eq     #0xbeff2c ; a0160054
   0xBEFC5C: cmp      x9, x24 ; 3f0118eb
   0xBEFC60: b.lo     #0xbefc6c ; 63000054
   0xBEFC64: udiv     x10, x9, x24 ; 2a09d89a
~~~

## Static PC 0x655E74 (word native_entry_candidate)

- ELF file offset: VA-to-ELF-segment-mapped; opcode: STATIC_FUNCTION_WINDOW; mask: pre_spawner_descriptor_builder
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x655E64: add      x0, sp, #0x30 ; e0c30091
   0x655E68: bl       #0x459bb4 ; 530ff897
   0x655E6C: mov      x25, xzr ; f9031faa
   0x655E70: b        #0x655830 ; 70feff17
>> 0x655E74: sub      sp, sp, #0x30 ; ffc300d1
   0x655E78: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x655E7C: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x655E80: add      x29, sp, #0x10 ; fd430091
   0x655E84: mov      x19, x8 ; f30308aa
   0x655E88: add      x0, x0, #0xa8 ; 00a00291
   0x655E8C: add      x8, sp, #8 ; e8230091
   0x655E90: mov      x20, x1 ; f40301aa
   0x655E94: bl       #0x5e8088 ; 7d48fe97
   0x655E98: ldr      x0, [sp, #8] ; e00740f9
   0x655E9C: cbz      x0, #0x655fbc ; 000900b4
   0x655EA0: ldr      x9, [x0, #0x48] ; 092440f9
   0x655EA4: cbz      x9, #0x656050 ; 690d00b4
   0x655EA8: fmov     d0, x9 ; 2001679e
   0x655EAC: cnt      v0.8b, v0.8b ; 0058200e
   0x655EB0: ldr      x8, [x20] ; 880240f9
   0x655EB4: uaddlv   h0, v0.8b ; 0038302e
   0x655EB8: fmov     w12, s0 ; 0c00261e
   0x655EBC: cmp      x12, #1 ; 9f0500f1
   0x655EC0: b.ls     #0x655f34 ; a9030054
   0x655EC4: cmp      x8, x9 ; 1f0109eb
   0x655EC8: b.lo     #0x655fec ; 23090054
   0x655ECC: udiv     x10, x8, x9 ; 0a09c99a
   0x655ED0: msub     x10, x10, x9, x8 ; 4aa1099b
   0x655ED4: ldr      x11, [x0, #0x40] ; 0b2040f9
   0x655ED8: ldr      x11, [x11, x10, lsl #3] ; 6b796af8
   0x655EDC: cbz      x11, #0x656050 ; ab0b00b4
   0x655EE0: ldr      x11, [x11] ; 6b0140f9
   0x655EE4: cbz      x11, #0x656050 ; 6b0b00b4
   0x655EE8: cmp      x12, #2 ; 9f0900f1
   0x655EEC: b.lo     #0x655f40 ; a3020054
   0x655EF0: ldr      x12, [x11, #8] ; 6c0540f9
   0x655EF4: cmp      x8, x12 ; 1f010ceb
   0x655EF8: b.ne     #0x655f0c ; a1000054
   0x655EFC: ldr      x12, [x11, #0x10] ; 6c0940f9
   0x655F00: cmp      x12, x8 ; 9f0108eb
   0x655F04: b.eq     #0x655f7c ; c0030054
   0x655F08: b        #0x655f24 ; 07000014
   0x655F0C: cmp      x12, x9 ; 9f0109eb
   0x655F10: b.lo     #0x655f1c ; 63000054
   0x655F14: udiv     x13, x12, x9 ; 8d09c99a
   0x655F18: msub     x12, x13, x9, x12 ; acb1099b
   0x655F1C: cmp      x12, x10 ; 9f010aeb
   0x655F20: b.ne     #0x655f2c ; 61000054
   0x655F24: ldr      x11, [x11] ; 6b0140f9
   0x655F28: cbnz     x11, #0x655ef0 ; 4bfeffb5
   0x655F2C: mov      w20, #1 ; 34008052
   0x655F30: b        #0x655f90 ; 18000014
   0x655F34: sub      x10, x9, #1 ; 2a0500d1
   0x655F38: and      x10, x10, x8 ; 4a01088a
   0x655F3C: b        #0x655ed4 ; e6ffff17
   0x655F40: sub      x9, x9, #1 ; 290500d1
   0x655F44: mov      w20, #1 ; 34008052
   0x655F48: ldr      x12, [x11, #8] ; 6c0540f9
   0x655F4C: cmp      x8, x12 ; 1f010ceb
   0x655F50: b.ne     #0x655f64 ; a1000054
   0x655F54: ldr      x12, [x11, #0x10] ; 6c0940f9
   0x655F58: cmp      x12, x8 ; 9f0108eb
   0x655F5C: b.eq     #0x655f7c ; 00010054
   0x655F60: b        #0x655f70 ; 04000014
   0x655F64: and      x12, x12, x9 ; 8c01098a
   0x655F68: cmp      x12, x10 ; 9f010aeb
   0x655F6C: b.ne     #0x655f2c ; 01feff54
   0x655F70: ldr      x11, [x11] ; 6b0140f9
   0x655F74: cbnz     x11, #0x655f48 ; abfeffb5
   0x655F78: b        #0x655f90 ; 06000014
   0x655F7C: ldr      x0, [x11, #0x18] ; 600d40f9
   0x655F80: mov      x8, x19 ; e80313aa
   0x655F84: bl       #0x5e7f98 ; 0548fe97
   0x655F88: ldr      x0, [sp, #8] ; e00740f9
   0x655F8C: mov      w20, wzr ; f4031f2a
   0x655F90: cbz      x0, #0x655fb8 ; 400100b4
   0x655F94: ldr      x8, [x0, #0x38] ; 081c40f9
   0x655F98: add      x10, x8, #0x1a ; 0a690091
   0x655F9C: ldaxrh   w9, [x10] ; 49fd5f48
   0x655FA0: sub      w11, w9, #1 ; 2b050051
   0x655FA4: stlxrh   w12, w11, [x10] ; 4bfd0c48
   0x655FA8: cbnz     w12, #0x655f9c ; acffff35
   0x655FAC: cmp      w9, #1 ; 3f050071
   0x655FB0: b.eq     #0x655ff4 ; 20020054
   0x655FB4: cbz      w9, #0x656038 ; 29040034
   0x655FB8: cbz      w20, #0x655fdc ; 34010034
   0x655FBC: add      x1, sp, #8 ; e1230091
   0x655FC0: mov      x0, x19 ; e00313aa
   0x655FC4: str      xzr, [x19] ; 7f0200f9
   0x655FC8: str      xzr, [sp, #8] ; ff0700f9
   0x655FCC: bl       #0x5e81a0 ; 7548fe97
   0x655FD0: tbz      w0, #0, #0x655fdc ; 60000036
   0x655FD4: ldr      x8, [sp, #8] ; e80740f9
   0x655FD8: str      x8, [x19] ; 680200f9
   0x655FDC: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x655FE0: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x655FE4: add      sp, sp, #0x30 ; ffc30091
   0x655FE8: ret       ; c0035fd6
   0x655FEC: mov      x10, x8 ; ea0308aa
   0x655FF0: b        #0x655ed4 ; b9ffff17
   0x655FF4: stp      xzr, xzr, [x8, #8] ; 1ffd00a9
   0x655FF8: ldr      x8, [x0, #0x38] ; 081c40f9
   0x655FFC: str      xzr, [x0, #0x38] ; 1f1c00f9
   0x656000: cbnz     x8, #0x656018 ; c80000b5
   0x656004: ldr      x8, [x0] ; 080040f9
   0x656008: ldr      x8, [x8, #0x50] ; 082940f9
   0x65600C: blr      x8 ; 00013fd6
   0x656010: tbnz     w20, #0, #0x655fbc ; 74fd0737
   0x656014: b        #0x655fdc ; f2ffff17
   0x656018: add      x10, x8, #0x18 ; 0a610091
   0x65601C: ldaxrh   w9, [x10] ; 49fd5f48
   0x656020: sub      w11, w9, #1 ; 2b050051
   0x656024: stlxrh   w12, w11, [x10] ; 4bfd0c48
   0x656028: cbnz     w12, #0x65601c ; acffff35
   0x65602C: cmp      w9, #1 ; 3f050071
   0x656030: b.eq     #0x65603c ; 60000054
   0x656034: cbnz     w9, #0x656004 ; 89feff35
   0x656038: bl       #0x3160640 ; 8229ac94
   0x65603C: str      x0, [sp] ; e00300f9
   0x656040: mov      x0, x8 ; e00308aa
   0x656044: bl       #0x6460 ; 07c1e697
   0x656048: ldr      x0, [sp] ; e00340f9
   0x65604C: b        #0x656004 ; eeffff17
   0x656050: mov      w20, #1 ; 34008052
   0x656054: b        #0x655f94 ; d0ffff17
   0x656058: strh     w1, [x0, #8] ; 01100079
   0x65605C: ret       ; c0035fd6
   0x656060: str      d8, [sp, #-0x70]! ; e80f19fc
   0x656064: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x656068: add      x29, sp, #0x10 ; fd430091
   0x65606C: stp      x28, x27, [sp, #0x20] ; fc6f02a9
   0x656070: stp      x26, x25, [sp, #0x30] ; fa6703a9
   0x656074: stp      x24, x23, [sp, #0x40] ; f85f04a9
   0x656078: stp      x22, x21, [sp, #0x50] ; f65705a9
   0x65607C: stp      x20, x19, [sp, #0x60] ; f44f06a9
   0x656080: sub      sp, sp, #0x230 ; ffc308d1
   0x656084: mov      x19, x8 ; f30308aa
   0x656088: mov      w8, #1 ; 28008052
   0x65608C: str      xzr, [sp, #0x18] ; ff0f00f9
   0x656090: strb     w8, [sp, #0x40] ; e8030139
   0x656094: mov      w8, #-0xff01 ; 08e09f12
   0x656098: mov      x25, #-1 ; 19008092
   0x65609C: stur     w8, [sp, #0x52] ; e82305b8
   0x6560A0: mov      w8, #0xffff ; e8ff9f52
   0x6560A4: mov      x21, x3 ; f50303aa
   0x6560A8: mov      w23, w2 ; f703022a
   0x6560AC: mov      x22, x1 ; f60301aa
   0x6560B0: strb     wzr, [sp, #0x20] ; ff830039
   0x6560B4: mov      x20, x0 ; f40300aa
   0x6560B8: add      x26, sp, #0x18 ; fa630091
   0x6560BC: strh     wzr, [sp, #0x46] ; ff8f0079
   0x6560C0: stp      x25, x25, [sp, #0x28] ; f9e702a9
   0x6560C4: strh     w8, [sp, #0x56] ; e8af0079
   0x6560C8: str      w8, [sp, #0x5c] ; e85f00b9
   0x6560CC: strb     wzr, [sp, #0x7e] ; fffb0139
   0x6560D0: str      w8, [sp, #0x80] ; e88300b9
   0x6560D4: bl       #0x3f0784 ; ac69f697
   0x6560D8: mov      w8, #4 ; 88008052
   0x6560DC: mov      w9, #0xf ; e9018052
   0x6560E0: movi     v0.2d, #0000000000000000 ; 00e4006f
   0x6560E4: strb     w8, [sp, #0x85] ; e8170239
   0x6560E8: mov      w8, #0xff ; e81f8052
   0x6560EC: strb     wzr, [sp, #0x98] ; ff630239
   0x6560F0: strb     w8, [sp, #0xad] ; e8b70239
   0x6560F4: ldrh     w8, [x20, #0x48] ; 88924079
   0x6560F8: ldrh     w24, [x20, #0x4a] ; 98964079
   0x6560FC: stp      q0, q0, [x26, #0xa0] ; 400305ad
   0x656100: strb     wzr, [sp, #0xb6] ; ffdb0239
   0x656104: str      xzr, [sp, #0x48] ; ff2700f9
   0x656108: str      x25, [sp, #0x60] ; f93300f9
   0x65610C: str      w25, [sp, #0x68] ; f96b00b9
   0x656110: strh     w8, [sp, #0x42] ; e8870079
   0x656114: ldrb     w8, [x0, #0x378] ; 08e04d39
   0x656118: mov      x0, x22 ; e00316aa
   0x65611C: stur     xzr, [x26, #0x89] ; 5f9308f8
   0x656120: stur     xzr, [x26, #0x81] ; 5f1308f8
   0x656124: stur     wzr, [x26, #0x91] ; 5f1309b8
   0x656128: stur     xzr, [x26, #0xe2] ; 5f230ef8
   0x65612C: stur     xzr, [x26, #0xda] ; 5fa30df8
   0x656130: strh     wzr, [sp, #0x10a] ; ff170279
   0x656134: stur     xzr, [x26, #0xea] ; 5fa30ef8
   0x656138: stur     xzr, [x26, #0x96] ; 5f6309f8
   0x65613C: stur     xzr, [sp, #0x6c] ; ffc306f8
   0x656140: strb     w8, [sp, #0x84] ; e8130239
   0x656144: ldp      w8, w10, [x20, #0x68] ; 882a4d29
   0x656148: sxtw     x8, w8 ; 087d4093
   0x65614C: orr      x8, x9, x8, lsl #4 ; 281108aa
   0x656150: ldrb     w9, [x21, #0x14] ; a9524039
   0x656154: cmp      w9, #0 ; 3f010071
   0x656158: mov      x9, #-0xfffd00000001 ; a9ffdf92
   0x65615C: movk     x9, #0, lsl #48 ; 0900e0f2
   0x656160: csel     x8, x8, x9, eq ; 0801899a
   0x656164: strb     w10, [sp, #0x58] ; ea630139
   0x656168: stur     xzr, [sp, #0x74] ; ff4307f8
   0x65616C: strh     wzr, [sp, #0x7c] ; fffb0079
   0x656170: str      x8, [sp, #0x38] ; e81f00f9
   0x656174: ldrh     w8, [x20, #0x64] ; 88ca4079
   0x656178: strh     w8, [sp, #0x44] ; e88b0079
   0x65617C: ldr      x8, [x22] ; c80240f9
   0x656180: str      q0, [x26, #0xc0] ; 4033803d
   0x656184: stp      xzr, xzr, [sp, #0x88] ; ffff08a9
   0x656188: stur     q0, [x26, #0xca] ; 40a38c3c
   0x65618C: ldrh     w26, [x20, #0x4c] ; 9a9a4079
   0x656190: ldr      x8, [x8, #0x18] ; 080d40f9
   0x656194: blr      x8 ; 00013fd6
   0x656198: ldr      x8, [x22] ; c80240f9
   0x65619C: mov      x0, x22 ; e00316aa
   0x6561A0: ldr      x8, [x8, #0x10] ; 080940f9
   0x6561A4: blr      x8 ; 00013fd6
   0x6561A8: subs     w8, w26, w24 ; 4803186b
   0x6561AC: b.eq     #0x6567fc ; 80320054
   0x6561B0: add      w8, w8, #1 ; 08050011
   0x6561B4: cbz      w8, #0x656ba0 ; 684f0034
   0x6561B8: clz      w9, w8 ; 0911c05a
   0x6561BC: ldp      x11, x12, [x0] ; 0b3040a9
   0x6561C0: lsl      w10, w8, w9 ; 0a21c91a
   0x6561C4: orr      w9, w9, #0x40 ; 29011a32
   0x6561C8: tst      w10, #0x7fffffff ; 5f790072
   0x6561CC: mov      x10, #-0x20 ; ea038092
   0x6561D0: cinc     x10, x10, eq ; 4a158a9a
   0x6561D4: add      x9, x10, x9 ; 4901098b
   0x6561D8: lsr      x9, x25, x9 ; 2927c99a
   0x6561DC: add      w10, w11, w12 ; 6a010c0b
   0x6561E0: eor      x13, x11, x12 ; 6d010cca
   0x6561E4: and      w10, w10, w9 ; 4a01090a
   0x6561E8: ror      x11, x11, #0x28 ; 6ba1cb93
   0x6561EC: eor      x11, x11, x13, lsl #16 ; 6b410dca
   0x6561F0: ror      x12, x13, #0x1b ; ac6dcd93
   0x6561F4: cmp      w8, w10 ; 1f010a6b
   0x6561F8: eor      x11, x11, x13 ; 6b010dca
   0x6561FC: b.ls     #0x6561dc ; 09ffff54
   0x656200: stp      x11, x12, [x0] ; 0b3000a9
   0x656204: ldr      w8, [x20, #0x60] ; 886240b9
   0x656208: add      w24, w24, w10 ; 18030a0b
   0x65620C: strh     w24, [sp, #0x50] ; f8a30079
   0x656210: tbnz     w8, #0x1f, #0x656218 ; 4800f837
   0x656214: strh     w8, [sp, #0x52] ; e8a70079
   0x656218: ldr      w8, [x20, #0x70] ; 887240b9
   0x65621C: tbz      w8, #0x1f, #0x6569dc ; 083ef836
   0x656220: ldr      w8, [x20, #0x78] ; 887a40b9
   0x656224: tst      w8, #0xff ; 1f1d0072
   0x656228: strb     w8, [sp, #0x7e] ; e8fb0139
   0x65622C: b.ne     #0x656260 ; a1010054
   0x656230: ldr      w8, [x20, #0x7c] ; 887e40b9
   0x656234: tbz      w8, #0x1f, #0x6569e4 ; 883df836
   0x656238: ldr      w8, [x20, #0x80] ; 888240b9
   0x65623C: tbz      w8, #0x1f, #0x6569ec ; 883df836
   0x656240: ldr      w8, [x20, #0x84] ; 888640b9
   0x656244: tbz      w8, #0x1f, #0x6569f4 ; 883df836
   0x656248: ldr      w8, [x20, #0x88] ; 888a40b9
   0x65624C: tbz      w8, #0x1f, #0x6569fc ; 883df836
   0x656250: ldr      w8, [x20, #0x8c] ; 888e40b9
   0x656254: tbz      w8, #0x1f, #0x656a04 ; 883df836
   0x656258: ldr      w8, [x20, #0x90] ; 889240b9
   0x65625C: tbz      w8, #0x1f, #0x656a0c ; 883df836
   0x656260: ldrb     w8, [x21, #4] ; a8124039
   0x656264: cbnz     w8, #0x656ac4 ; 08430035
   0x656268: add      x8, x20, #0x74 ; 88d20191
   0x65626C: ldr      w8, [x8] ; 080140b9
   0x656270: tbnz     w8, #0x1f, #0x656278 ; 4800f837
   0x656274: strh     w8, [sp, #0x80] ; e8030179
   0x656278: ldr      s0, [x20, #0x50] ; 805240bd
   0x65627C: add      w8, w23, #1 ; e8060011
   0x656280: strb     w8, [sp, #0x40] ; e8030139
   0x656284: fcmp     s0, #0.0 ; 0820201e
   0x656288: b.hi     #0x656594 ; 68180054
   0x65628C: ldrb     w8, [x21, #0x12] ; a84a4039
   0x656290: cbnz     w8, #0x656a14 ; 283c0035
   0x656294: add      x0, sp, #0x18 ; e0630091
   0x656298: bl       #0x656f80 ; 3a030094
   0x65629C: ldr      x0, [x20, #8] ; 800640f9
   0x6562A0: add      x1, sp, #0x18 ; e1630091
   0x6562A4: mov      x8, x19 ; e80313aa
   0x6562A8: bl       #0x656ca4 ; 7f020094
   0x6562AC: ldr      x0, [x19] ; 600240f9
   0x6562B0: ldr      x8, [x0] ; 080040f9
   0x6562B4: ldr      x8, [x8, #0x1c8] ; 08e540f9
   0x6562B8: blr      x8 ; 00013fd6
   0x6562BC: ldr      x22, [x19] ; 760240f9
   0x6562C0: mov      w21, w0 ; f503002a
   0x6562C4: cbz      x22, #0x6562f8 ; b60100b4
   0x6562C8: ldr      x23, [x22, #0x38] ; d71e40f9
   0x6562CC: ldr      x8, [x23, #0x10] ; e80a40f9
   0x6562D0: cbz      x8, #0x656b8c ; e84500b4
   0x6562D4: add      x9, x23, #0x1a ; e96a0091
~~~

## Static PC 0x5E7AD4 (word native_entry_candidate)

- ELF file offset: VA-to-ELF-segment-mapped; opcode: STATIC_FUNCTION_WINDOW; mask: shared_descriptor_lookup
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x5E7AC4: ccmp     x0, #0, #4, ne ; 041840fa
   0x5E7AC8: b.ne     #0x5e7abc ; a1ffff54
   0x5E7ACC: cbnz     x0, #0x5e79f0 ; 20f9ffb5
   0x5E7AD0: b        #0x5e7a58 ; e2ffff17
>> 0x5E7AD4: sub      sp, sp, #0x20 ; ff8300d1
   0x5E7AD8: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x5E7ADC: add      x29, sp, #0x10 ; fd430091
   0x5E7AE0: ldr      x10, [x0] ; 0a0040f9
   0x5E7AE4: cbz      x10, #0x5e7b24 ; 0a0200b4
   0x5E7AE8: adrp     x11, #0x3ec2000 ; cbc601f0
   0x5E7AEC: and      x9, x10, #0xfffff ; 494d4092
   0x5E7AF0: ldr      x11, [x11, #0x1c8] ; 6be540f9
   0x5E7AF4: add      x11, x11, x9, lsl #5 ; 6b15098b
   0x5E7AF8: add      x1, x11, #0x10 ; 61410091
   0x5E7AFC: add      x9, x11, #0x28 ; 69a10091
   0x5E7B00: ldaxrh   w12, [x9] ; 2cfd5f48
   0x5E7B04: add      w13, w12, #1 ; 8d050011
   0x5E7B08: stlxrh   w14, w13, [x9] ; 2dfd0e48
   0x5E7B0C: cbnz     w14, #0x5e7b00 ; aeffff35
   0x5E7B10: cbnz     w12, #0x5e7b34 ; 2c010035
   0x5E7B14: ldaxrh   w10, [x9] ; 2afd5f48
   0x5E7B18: sub      w10, w10, #1 ; 4a050051
   0x5E7B1C: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x5E7B20: cbnz     w11, #0x5e7b14 ; abffff35
   0x5E7B24: str      xzr, [x8] ; 1f0100f9
   0x5E7B28: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x5E7B2C: add      sp, sp, #0x20 ; ff830091
   0x5E7B30: ret       ; c0035fd6
   0x5E7B34: add      x11, x11, #0x2c ; 6bb10091
   0x5E7B38: ldar     w11, [x11] ; 6bfddf88
   0x5E7B3C: ldr      x12, [x1] ; 2c0040f9
   0x5E7B40: cmn      w11, #1 ; 7f050031
   0x5E7B44: ccmp     x12, x10, #0, ne ; 80114afa
   0x5E7B48: b.ne     #0x5e7b14 ; 61feff54
   0x5E7B4C: add      x0, sp, #8 ; e0230091
   0x5E7B50: stp      x8, xzr, [sp] ; e87f00a9
   0x5E7B54: bl       #0x6400 ; 2b7ae897
   0x5E7B58: ldp      x8, x0, [sp] ; e80340a9
   0x5E7B5C: cbz      x0, #0x5e7b24 ; 40feffb4
   0x5E7B60: ldrh     w10, [x0, #0x1a] ; 0a344079
   0x5E7B64: cbz      w10, #0x5e7bdc ; ca030034
   0x5E7B68: add      x8, x0, #0x1a ; 08680091
   0x5E7B6C: ldxrh    w9, [x8] ; 097d5f48
   0x5E7B70: cmp      w9, w10, uxth ; 3f212a6b
   0x5E7B74: b.ne     #0x5e7b8c ; c1000054
   0x5E7B78: add      w10, w10, #1 ; 4a050011
   0x5E7B7C: stxrh    w11, w10, [x8] ; 0a7d0b48
   0x5E7B80: cbnz     w11, #0x5e7b90 ; 8b000035
   0x5E7B84: mov      w10, #1 ; 2a008052
   0x5E7B88: b        #0x5e7b94 ; 03000014
   0x5E7B8C: clrex     ; 5f3f03d5
   0x5E7B90: mov      w10, wzr ; ea031f2a
   0x5E7B94: cbz      w10, #0x5e7be4 ; 8a020034
   0x5E7B98: ldr      x8, [x0, #0x10] ; 080840f9
   0x5E7B9C: sub      x9, x8, #0x28 ; 09a100d1
   0x5E7BA0: cmp      x8, #0 ; 1f0100f1
   0x5E7BA4: csel     x11, xzr, x9, eq ; eb03899a
   0x5E7BA8: ldr      x8, [sp] ; e80340f9
   0x5E7BAC: add      x9, x0, #0x18 ; 09600091
   0x5E7BB0: str      x11, [x8] ; 0b0100f9
   0x5E7BB4: ldaxrh   w8, [x9] ; 28fd5f48
   0x5E7BB8: sub      w10, w8, #1 ; 0a050051
   0x5E7BBC: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x5E7BC0: cbnz     w11, #0x5e7bb4 ; abffff35
   0x5E7BC4: cmp      w8, #1 ; 1f050071
   0x5E7BC8: b.eq     #0x5e7bd4 ; 60000054
   0x5E7BCC: cbnz     w8, #0x5e7b28 ; e8faff35
   0x5E7BD0: bl       #0x3160640 ; 9ce2ad94
   0x5E7BD4: bl       #0x6460 ; 237ae897
   0x5E7BD8: b        #0x5e7b28 ; d4ffff17
   0x5E7BDC: mov      x11, xzr ; eb031faa
   0x5E7BE0: b        #0x5e7ba8 ; f2ffff17
   0x5E7BE4: mov      x11, xzr ; eb031faa
   0x5E7BE8: mov      w10, w9 ; ea03092a
   0x5E7BEC: cbnz     w9, #0x5e7b6c ; 09fcff35
   0x5E7BF0: b        #0x5e7ba8 ; eeffff17
   0x5E7BF4: sub      sp, sp, #0x30 ; ffc300d1
   0x5E7BF8: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x5E7BFC: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x5E7C00: add      x29, sp, #0x10 ; fd430091
   0x5E7C04: ldr      x10, [x0, #0x1b0] ; 0ad840f9
   0x5E7C08: cbz      x10, #0x5e7c48 ; 0a0200b4
   0x5E7C0C: adrp     x9, #0x3ec2000 ; c9c601f0
   0x5E7C10: and      x8, x10, #0xfffff ; 484d4092
   0x5E7C14: ldr      x9, [x9, #0x1c8] ; 29e540f9
   0x5E7C18: add      x11, x9, x8, lsl #5 ; 2b15088b
   0x5E7C1C: add      x8, x11, #0x10 ; 68410091
   0x5E7C20: add      x9, x11, #0x28 ; 69a10091
   0x5E7C24: ldaxrh   w12, [x9] ; 2cfd5f48
   0x5E7C28: add      w13, w12, #1 ; 8d050011
   0x5E7C2C: stlxrh   w14, w13, [x9] ; 2dfd0e48
   0x5E7C30: cbnz     w14, #0x5e7c24 ; aeffff35
   0x5E7C34: cbnz     w12, #0x5e7c60 ; 6c010035
   0x5E7C38: ldaxrh   w8, [x9] ; 28fd5f48
   0x5E7C3C: sub      w8, w8, #1 ; 08050051
   0x5E7C40: stlxrh   w10, w8, [x9] ; 28fd0a48
   0x5E7C44: cbnz     w10, #0x5e7c38 ; aaffff35
   0x5E7C48: mov      w8, wzr ; e8031f2a
   0x5E7C4C: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x5E7C50: and      w0, w8, #1 ; 00010012
   0x5E7C54: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x5E7C58: add      sp, sp, #0x30 ; ffc30091
   0x5E7C5C: ret       ; c0035fd6
   0x5E7C60: add      x11, x11, #0x2c ; 6bb10091
   0x5E7C64: ldar     w11, [x11] ; 6bfddf88
   0x5E7C68: ldr      x12, [x8] ; 0c0140f9
   0x5E7C6C: cmn      w11, #1 ; 7f050031
   0x5E7C70: ccmp     x12, x10, #0, ne ; 80114afa
   0x5E7C74: b.ne     #0x5e7c38 ; 21feff54
   0x5E7C78: stp      x1, xzr, [sp] ; e17f00a9
   0x5E7C7C: add      x0, sp, #8 ; e0230091
   0x5E7C80: mov      x1, x8 ; e10308aa
   0x5E7C84: bl       #0x6400 ; df79e897
   0x5E7C88: ldr      x0, [sp, #8] ; e00740f9
   0x5E7C8C: cbz      x0, #0x5e7c48 ; e0fdffb4
   0x5E7C90: ldrh     w10, [x0, #0x1a] ; 0a344079
   0x5E7C94: cbz      w10, #0x5e7dac ; ca080034
   0x5E7C98: add      x8, x0, #0x1a ; 08680091
   0x5E7C9C: ldxrh    w9, [x8] ; 097d5f48
   0x5E7CA0: cmp      w9, w10, uxth ; 3f212a6b
   0x5E7CA4: b.ne     #0x5e7cbc ; c1000054
   0x5E7CA8: add      w10, w10, #1 ; 4a050011
   0x5E7CAC: stxrh    w11, w10, [x8] ; 0a7d0b48
   0x5E7CB0: cbnz     w11, #0x5e7cc0 ; 8b000035
   0x5E7CB4: mov      w10, #1 ; 2a008052
   0x5E7CB8: b        #0x5e7cc4 ; 03000014
   0x5E7CBC: clrex     ; 5f3f03d5
   0x5E7CC0: mov      w10, wzr ; ea031f2a
   0x5E7CC4: cbz      w10, #0x5e7da4 ; 0a070034
   0x5E7CC8: ldr      x8, [x0, #0x10] ; 080840f9
   0x5E7CCC: sub      x9, x8, #0x28 ; 09a100d1
   0x5E7CD0: cmp      x8, #0 ; 1f0100f1
   0x5E7CD4: csel     x19, xzr, x9, eq ; f303899a
   0x5E7CD8: add      x9, x0, #0x18 ; 09600091
   0x5E7CDC: ldaxrh   w8, [x9] ; 28fd5f48
   0x5E7CE0: sub      w10, w8, #1 ; 0a050051
   0x5E7CE4: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x5E7CE8: cbnz     w11, #0x5e7cdc ; abffff35
   0x5E7CEC: cmp      w8, #1 ; 1f050071
   0x5E7CF0: b.eq     #0x5e7d48 ; c0020054
   0x5E7CF4: cbz      w8, #0x5e7d94 ; 08050034
   0x5E7CF8: cbz      x19, #0x5e7c48 ; 93faffb4
   0x5E7CFC: ldr      x20, [x19, #0xe0] ; 747240f9
   0x5E7D00: cbz      x20, #0x5e7da0 ; 140500b4
   0x5E7D04: ldr      x9, [x20, #0x60] ; 893240f9
   0x5E7D08: ldr      x8, [sp] ; e80340f9
   0x5E7D0C: lsr      x8, x9, x8 ; 2825c89a
   0x5E7D10: and      w8, w8, #1 ; 08010012
   0x5E7D14: str      w8, [sp] ; e80300b9
   0x5E7D18: ldr      x8, [x19, #0x38] ; 681e40f9
   0x5E7D1C: add      x10, x8, #0x1a ; 0a690091
   0x5E7D20: ldaxrh   w9, [x10] ; 49fd5f48
   0x5E7D24: sub      w11, w9, #1 ; 2b050051
   0x5E7D28: stlxrh   w12, w11, [x10] ; 4bfd0c48
   0x5E7D2C: cbnz     w12, #0x5e7d20 ; acffff35
   0x5E7D30: cmp      w9, #1 ; 3f050071
   0x5E7D34: b.eq     #0x5e7d50 ; e0000054
   0x5E7D38: cbz      w9, #0x5e7d94 ; e9020034
   0x5E7D3C: ldr      w8, [sp] ; e80340b9
   0x5E7D40: cbnz     x20, #0x5e7c4c ; 74f8ffb5
   0x5E7D44: b        #0x5e7c48 ; c1ffff17
   0x5E7D48: bl       #0x6460 ; c679e897
   0x5E7D4C: b        #0x5e7cf8 ; ebffff17
   0x5E7D50: stp      xzr, xzr, [x8, #8] ; 1ffd00a9
   0x5E7D54: ldr      x0, [x19, #0x38] ; 601e40f9
   0x5E7D58: str      xzr, [x19, #0x38] ; 7f1e00f9
   0x5E7D5C: cbnz     x0, #0x5e7d74 ; c00000b5
   0x5E7D60: ldr      x8, [x19] ; 680240f9
   0x5E7D64: mov      x0, x19 ; e00313aa
   0x5E7D68: ldr      x8, [x8, #0x50] ; 082940f9
   0x5E7D6C: blr      x8 ; 00013fd6
   0x5E7D70: b        #0x5e7d3c ; f3ffff17
   0x5E7D74: add      x9, x0, #0x18 ; 09600091
   0x5E7D78: ldaxrh   w8, [x9] ; 28fd5f48
   0x5E7D7C: sub      w10, w8, #1 ; 0a050051
   0x5E7D80: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x5E7D84: cbnz     w11, #0x5e7d78 ; abffff35
   0x5E7D88: cmp      w8, #1 ; 1f050071
   0x5E7D8C: b.eq     #0x5e7d98 ; 60000054
   0x5E7D90: cbnz     w8, #0x5e7d60 ; 88feff35
   0x5E7D94: bl       #0x3160640 ; 2be2ad94
   0x5E7D98: bl       #0x6460 ; b279e897
   0x5E7D9C: b        #0x5e7d60 ; f1ffff17
   0x5E7DA0: b        #0x5e7d18 ; deffff17
   0x5E7DA4: mov      w10, w9 ; ea03092a
   0x5E7DA8: cbnz     w9, #0x5e7c9c ; a9f7ff35
   0x5E7DAC: mov      x19, xzr ; f3031faa
   0x5E7DB0: b        #0x5e7cd8 ; caffff17
   0x5E7DB4: sub      sp, sp, #0x30 ; ffc300d1
   0x5E7DB8: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x5E7DBC: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x5E7DC0: add      x29, sp, #0x10 ; fd430091
   0x5E7DC4: mov      x19, x8 ; f30308aa
   0x5E7DC8: add      x0, x0, #0xa0 ; 00800291
   0x5E7DCC: add      x8, sp, #8 ; e8230091
   0x5E7DD0: mov      x20, x1 ; f40301aa
   0x5E7DD4: bl       #0x5e8088 ; ad000094
   0x5E7DD8: ldr      x0, [sp, #8] ; e00740f9
   0x5E7DDC: cbz      x0, #0x5e7efc ; 000900b4
   0x5E7DE0: ldr      x9, [x0, #0x48] ; 092440f9
   0x5E7DE4: cbz      x9, #0x5e7f90 ; 690d00b4
   0x5E7DE8: fmov     d0, x9 ; 2001679e
   0x5E7DEC: cnt      v0.8b, v0.8b ; 0058200e
   0x5E7DF0: ldr      x8, [x20] ; 880240f9
   0x5E7DF4: uaddlv   h0, v0.8b ; 0038302e
   0x5E7DF8: fmov     w12, s0 ; 0c00261e
   0x5E7DFC: cmp      x12, #1 ; 9f0500f1
   0x5E7E00: b.ls     #0x5e7e74 ; a9030054
   0x5E7E04: cmp      x8, x9 ; 1f0109eb
   0x5E7E08: b.lo     #0x5e7f2c ; 23090054
   0x5E7E0C: udiv     x10, x8, x9 ; 0a09c99a
   0x5E7E10: msub     x10, x10, x9, x8 ; 4aa1099b
   0x5E7E14: ldr      x11, [x0, #0x40] ; 0b2040f9
   0x5E7E18: ldr      x11, [x11, x10, lsl #3] ; 6b796af8
   0x5E7E1C: cbz      x11, #0x5e7f90 ; ab0b00b4
   0x5E7E20: ldr      x11, [x11] ; 6b0140f9
   0x5E7E24: cbz      x11, #0x5e7f90 ; 6b0b00b4
   0x5E7E28: cmp      x12, #2 ; 9f0900f1
   0x5E7E2C: b.lo     #0x5e7e80 ; a3020054
   0x5E7E30: ldr      x12, [x11, #8] ; 6c0540f9
   0x5E7E34: cmp      x8, x12 ; 1f010ceb
   0x5E7E38: b.ne     #0x5e7e4c ; a1000054
   0x5E7E3C: ldr      x12, [x11, #0x10] ; 6c0940f9
   0x5E7E40: cmp      x12, x8 ; 9f0108eb
   0x5E7E44: b.eq     #0x5e7ebc ; c0030054
   0x5E7E48: b        #0x5e7e64 ; 07000014
   0x5E7E4C: cmp      x12, x9 ; 9f0109eb
   0x5E7E50: b.lo     #0x5e7e5c ; 63000054
   0x5E7E54: udiv     x13, x12, x9 ; 8d09c99a
   0x5E7E58: msub     x12, x13, x9, x12 ; acb1099b
   0x5E7E5C: cmp      x12, x10 ; 9f010aeb
   0x5E7E60: b.ne     #0x5e7e6c ; 61000054
   0x5E7E64: ldr      x11, [x11] ; 6b0140f9
   0x5E7E68: cbnz     x11, #0x5e7e30 ; 4bfeffb5
   0x5E7E6C: mov      w20, #1 ; 34008052
   0x5E7E70: b        #0x5e7ed0 ; 18000014
   0x5E7E74: sub      x10, x9, #1 ; 2a0500d1
   0x5E7E78: and      x10, x10, x8 ; 4a01088a
   0x5E7E7C: b        #0x5e7e14 ; e6ffff17
   0x5E7E80: sub      x9, x9, #1 ; 290500d1
   0x5E7E84: mov      w20, #1 ; 34008052
   0x5E7E88: ldr      x12, [x11, #8] ; 6c0540f9
   0x5E7E8C: cmp      x8, x12 ; 1f010ceb
   0x5E7E90: b.ne     #0x5e7ea4 ; a1000054
   0x5E7E94: ldr      x12, [x11, #0x10] ; 6c0940f9
   0x5E7E98: cmp      x12, x8 ; 9f0108eb
   0x5E7E9C: b.eq     #0x5e7ebc ; 00010054
   0x5E7EA0: b        #0x5e7eb0 ; 04000014
   0x5E7EA4: and      x12, x12, x9 ; 8c01098a
   0x5E7EA8: cmp      x12, x10 ; 9f010aeb
   0x5E7EAC: b.ne     #0x5e7e6c ; 01feff54
   0x5E7EB0: ldr      x11, [x11] ; 6b0140f9
   0x5E7EB4: cbnz     x11, #0x5e7e88 ; abfeffb5
   0x5E7EB8: b        #0x5e7ed0 ; 06000014
   0x5E7EBC: ldr      x0, [x11, #0x18] ; 600d40f9
   0x5E7EC0: mov      x8, x19 ; e80313aa
   0x5E7EC4: bl       #0x5e7f98 ; 35000094
   0x5E7EC8: ldr      x0, [sp, #8] ; e00740f9
   0x5E7ECC: mov      w20, wzr ; f4031f2a
   0x5E7ED0: cbz      x0, #0x5e7ef8 ; 400100b4
   0x5E7ED4: ldr      x8, [x0, #0x38] ; 081c40f9
   0x5E7ED8: add      x10, x8, #0x1a ; 0a690091
   0x5E7EDC: ldaxrh   w9, [x10] ; 49fd5f48
   0x5E7EE0: sub      w11, w9, #1 ; 2b050051
   0x5E7EE4: stlxrh   w12, w11, [x10] ; 4bfd0c48
   0x5E7EE8: cbnz     w12, #0x5e7edc ; acffff35
   0x5E7EEC: cmp      w9, #1 ; 3f050071
   0x5E7EF0: b.eq     #0x5e7f34 ; 20020054
   0x5E7EF4: cbz      w9, #0x5e7f78 ; 29040034
   0x5E7EF8: cbz      w20, #0x5e7f1c ; 34010034
   0x5E7EFC: add      x1, sp, #8 ; e1230091
   0x5E7F00: mov      x0, x19 ; e00313aa
   0x5E7F04: str      xzr, [x19] ; 7f0200f9
   0x5E7F08: str      xzr, [sp, #8] ; ff0700f9
   0x5E7F0C: bl       #0x5e81a0 ; a5000094
   0x5E7F10: tbz      w0, #0, #0x5e7f1c ; 60000036
   0x5E7F14: ldr      x8, [sp, #8] ; e80740f9
   0x5E7F18: str      x8, [x19] ; 680200f9
   0x5E7F1C: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x5E7F20: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x5E7F24: add      sp, sp, #0x30 ; ffc30091
   0x5E7F28: ret       ; c0035fd6
   0x5E7F2C: mov      x10, x8 ; ea0308aa
   0x5E7F30: b        #0x5e7e14 ; b9ffff17
   0x5E7F34: stp      xzr, xzr, [x8, #8] ; 1ffd00a9
~~~

## Static PC 0x656060 (word native_entry_candidate)

- ELF file offset: VA-to-ELF-segment-mapped; opcode: STATIC_FUNCTION_WINDOW; mask: native_mode_state_builder
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x656050: mov      w20, #1 ; 34008052
   0x656054: b        #0x655f94 ; d0ffff17
   0x656058: strh     w1, [x0, #8] ; 01100079
   0x65605C: ret       ; c0035fd6
>> 0x656060: str      d8, [sp, #-0x70]! ; e80f19fc
   0x656064: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x656068: add      x29, sp, #0x10 ; fd430091
   0x65606C: stp      x28, x27, [sp, #0x20] ; fc6f02a9
   0x656070: stp      x26, x25, [sp, #0x30] ; fa6703a9
   0x656074: stp      x24, x23, [sp, #0x40] ; f85f04a9
   0x656078: stp      x22, x21, [sp, #0x50] ; f65705a9
   0x65607C: stp      x20, x19, [sp, #0x60] ; f44f06a9
   0x656080: sub      sp, sp, #0x230 ; ffc308d1
   0x656084: mov      x19, x8 ; f30308aa
   0x656088: mov      w8, #1 ; 28008052
   0x65608C: str      xzr, [sp, #0x18] ; ff0f00f9
   0x656090: strb     w8, [sp, #0x40] ; e8030139
   0x656094: mov      w8, #-0xff01 ; 08e09f12
   0x656098: mov      x25, #-1 ; 19008092
   0x65609C: stur     w8, [sp, #0x52] ; e82305b8
   0x6560A0: mov      w8, #0xffff ; e8ff9f52
   0x6560A4: mov      x21, x3 ; f50303aa
   0x6560A8: mov      w23, w2 ; f703022a
   0x6560AC: mov      x22, x1 ; f60301aa
   0x6560B0: strb     wzr, [sp, #0x20] ; ff830039
   0x6560B4: mov      x20, x0 ; f40300aa
   0x6560B8: add      x26, sp, #0x18 ; fa630091
   0x6560BC: strh     wzr, [sp, #0x46] ; ff8f0079
   0x6560C0: stp      x25, x25, [sp, #0x28] ; f9e702a9
   0x6560C4: strh     w8, [sp, #0x56] ; e8af0079
   0x6560C8: str      w8, [sp, #0x5c] ; e85f00b9
   0x6560CC: strb     wzr, [sp, #0x7e] ; fffb0139
   0x6560D0: str      w8, [sp, #0x80] ; e88300b9
   0x6560D4: bl       #0x3f0784 ; ac69f697
   0x6560D8: mov      w8, #4 ; 88008052
   0x6560DC: mov      w9, #0xf ; e9018052
   0x6560E0: movi     v0.2d, #0000000000000000 ; 00e4006f
   0x6560E4: strb     w8, [sp, #0x85] ; e8170239
   0x6560E8: mov      w8, #0xff ; e81f8052
   0x6560EC: strb     wzr, [sp, #0x98] ; ff630239
   0x6560F0: strb     w8, [sp, #0xad] ; e8b70239
   0x6560F4: ldrh     w8, [x20, #0x48] ; 88924079
   0x6560F8: ldrh     w24, [x20, #0x4a] ; 98964079
   0x6560FC: stp      q0, q0, [x26, #0xa0] ; 400305ad
   0x656100: strb     wzr, [sp, #0xb6] ; ffdb0239
   0x656104: str      xzr, [sp, #0x48] ; ff2700f9
   0x656108: str      x25, [sp, #0x60] ; f93300f9
   0x65610C: str      w25, [sp, #0x68] ; f96b00b9
   0x656110: strh     w8, [sp, #0x42] ; e8870079
   0x656114: ldrb     w8, [x0, #0x378] ; 08e04d39
   0x656118: mov      x0, x22 ; e00316aa
   0x65611C: stur     xzr, [x26, #0x89] ; 5f9308f8
   0x656120: stur     xzr, [x26, #0x81] ; 5f1308f8
   0x656124: stur     wzr, [x26, #0x91] ; 5f1309b8
   0x656128: stur     xzr, [x26, #0xe2] ; 5f230ef8
   0x65612C: stur     xzr, [x26, #0xda] ; 5fa30df8
   0x656130: strh     wzr, [sp, #0x10a] ; ff170279
   0x656134: stur     xzr, [x26, #0xea] ; 5fa30ef8
   0x656138: stur     xzr, [x26, #0x96] ; 5f6309f8
   0x65613C: stur     xzr, [sp, #0x6c] ; ffc306f8
   0x656140: strb     w8, [sp, #0x84] ; e8130239
   0x656144: ldp      w8, w10, [x20, #0x68] ; 882a4d29
   0x656148: sxtw     x8, w8 ; 087d4093
   0x65614C: orr      x8, x9, x8, lsl #4 ; 281108aa
   0x656150: ldrb     w9, [x21, #0x14] ; a9524039
   0x656154: cmp      w9, #0 ; 3f010071
   0x656158: mov      x9, #-0xfffd00000001 ; a9ffdf92
   0x65615C: movk     x9, #0, lsl #48 ; 0900e0f2
   0x656160: csel     x8, x8, x9, eq ; 0801899a
   0x656164: strb     w10, [sp, #0x58] ; ea630139
   0x656168: stur     xzr, [sp, #0x74] ; ff4307f8
   0x65616C: strh     wzr, [sp, #0x7c] ; fffb0079
   0x656170: str      x8, [sp, #0x38] ; e81f00f9
   0x656174: ldrh     w8, [x20, #0x64] ; 88ca4079
   0x656178: strh     w8, [sp, #0x44] ; e88b0079
   0x65617C: ldr      x8, [x22] ; c80240f9
   0x656180: str      q0, [x26, #0xc0] ; 4033803d
   0x656184: stp      xzr, xzr, [sp, #0x88] ; ffff08a9
   0x656188: stur     q0, [x26, #0xca] ; 40a38c3c
   0x65618C: ldrh     w26, [x20, #0x4c] ; 9a9a4079
   0x656190: ldr      x8, [x8, #0x18] ; 080d40f9
   0x656194: blr      x8 ; 00013fd6
   0x656198: ldr      x8, [x22] ; c80240f9
   0x65619C: mov      x0, x22 ; e00316aa
   0x6561A0: ldr      x8, [x8, #0x10] ; 080940f9
   0x6561A4: blr      x8 ; 00013fd6
   0x6561A8: subs     w8, w26, w24 ; 4803186b
   0x6561AC: b.eq     #0x6567fc ; 80320054
   0x6561B0: add      w8, w8, #1 ; 08050011
   0x6561B4: cbz      w8, #0x656ba0 ; 684f0034
   0x6561B8: clz      w9, w8 ; 0911c05a
   0x6561BC: ldp      x11, x12, [x0] ; 0b3040a9
   0x6561C0: lsl      w10, w8, w9 ; 0a21c91a
   0x6561C4: orr      w9, w9, #0x40 ; 29011a32
   0x6561C8: tst      w10, #0x7fffffff ; 5f790072
   0x6561CC: mov      x10, #-0x20 ; ea038092
   0x6561D0: cinc     x10, x10, eq ; 4a158a9a
   0x6561D4: add      x9, x10, x9 ; 4901098b
   0x6561D8: lsr      x9, x25, x9 ; 2927c99a
   0x6561DC: add      w10, w11, w12 ; 6a010c0b
   0x6561E0: eor      x13, x11, x12 ; 6d010cca
   0x6561E4: and      w10, w10, w9 ; 4a01090a
   0x6561E8: ror      x11, x11, #0x28 ; 6ba1cb93
   0x6561EC: eor      x11, x11, x13, lsl #16 ; 6b410dca
   0x6561F0: ror      x12, x13, #0x1b ; ac6dcd93
   0x6561F4: cmp      w8, w10 ; 1f010a6b
   0x6561F8: eor      x11, x11, x13 ; 6b010dca
   0x6561FC: b.ls     #0x6561dc ; 09ffff54
   0x656200: stp      x11, x12, [x0] ; 0b3000a9
   0x656204: ldr      w8, [x20, #0x60] ; 886240b9
   0x656208: add      w24, w24, w10 ; 18030a0b
   0x65620C: strh     w24, [sp, #0x50] ; f8a30079
   0x656210: tbnz     w8, #0x1f, #0x656218 ; 4800f837
   0x656214: strh     w8, [sp, #0x52] ; e8a70079
   0x656218: ldr      w8, [x20, #0x70] ; 887240b9
   0x65621C: tbz      w8, #0x1f, #0x6569dc ; 083ef836
   0x656220: ldr      w8, [x20, #0x78] ; 887a40b9
   0x656224: tst      w8, #0xff ; 1f1d0072
   0x656228: strb     w8, [sp, #0x7e] ; e8fb0139
   0x65622C: b.ne     #0x656260 ; a1010054
   0x656230: ldr      w8, [x20, #0x7c] ; 887e40b9
   0x656234: tbz      w8, #0x1f, #0x6569e4 ; 883df836
   0x656238: ldr      w8, [x20, #0x80] ; 888240b9
   0x65623C: tbz      w8, #0x1f, #0x6569ec ; 883df836
   0x656240: ldr      w8, [x20, #0x84] ; 888640b9
   0x656244: tbz      w8, #0x1f, #0x6569f4 ; 883df836
   0x656248: ldr      w8, [x20, #0x88] ; 888a40b9
   0x65624C: tbz      w8, #0x1f, #0x6569fc ; 883df836
   0x656250: ldr      w8, [x20, #0x8c] ; 888e40b9
   0x656254: tbz      w8, #0x1f, #0x656a04 ; 883df836
   0x656258: ldr      w8, [x20, #0x90] ; 889240b9
   0x65625C: tbz      w8, #0x1f, #0x656a0c ; 883df836
   0x656260: ldrb     w8, [x21, #4] ; a8124039
   0x656264: cbnz     w8, #0x656ac4 ; 08430035
   0x656268: add      x8, x20, #0x74 ; 88d20191
   0x65626C: ldr      w8, [x8] ; 080140b9
   0x656270: tbnz     w8, #0x1f, #0x656278 ; 4800f837
   0x656274: strh     w8, [sp, #0x80] ; e8030179
   0x656278: ldr      s0, [x20, #0x50] ; 805240bd
   0x65627C: add      w8, w23, #1 ; e8060011
   0x656280: strb     w8, [sp, #0x40] ; e8030139
   0x656284: fcmp     s0, #0.0 ; 0820201e
   0x656288: b.hi     #0x656594 ; 68180054
   0x65628C: ldrb     w8, [x21, #0x12] ; a84a4039
   0x656290: cbnz     w8, #0x656a14 ; 283c0035
   0x656294: add      x0, sp, #0x18 ; e0630091
   0x656298: bl       #0x656f80 ; 3a030094
   0x65629C: ldr      x0, [x20, #8] ; 800640f9
   0x6562A0: add      x1, sp, #0x18 ; e1630091
   0x6562A4: mov      x8, x19 ; e80313aa
   0x6562A8: bl       #0x656ca4 ; 7f020094
   0x6562AC: ldr      x0, [x19] ; 600240f9
   0x6562B0: ldr      x8, [x0] ; 080040f9
   0x6562B4: ldr      x8, [x8, #0x1c8] ; 08e540f9
   0x6562B8: blr      x8 ; 00013fd6
   0x6562BC: ldr      x22, [x19] ; 760240f9
   0x6562C0: mov      w21, w0 ; f503002a
   0x6562C4: cbz      x22, #0x6562f8 ; b60100b4
   0x6562C8: ldr      x23, [x22, #0x38] ; d71e40f9
   0x6562CC: ldr      x8, [x23, #0x10] ; e80a40f9
   0x6562D0: cbz      x8, #0x656b8c ; e84500b4
   0x6562D4: add      x9, x23, #0x1a ; e96a0091
   0x6562D8: ldaxrh   w8, [x9] ; 28fd5f48
   0x6562DC: add      w10, w8, #1 ; 0a050011
   0x6562E0: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x6562E4: cbnz     w11, #0x6562d8 ; abffff35
   0x6562E8: cbz      w8, #0x656804 ; e8280034
   0x6562EC: mov      w9, #0xffff ; e9ff9f52
   0x6562F0: cmp      w8, w9 ; 1f01096b
   0x6562F4: b.eq     #0x656b8c ; c0440054
   0x6562F8: ldur     q0, [x20, #0xac] ; 80c2ca3c
   0x6562FC: mov      x0, x22 ; e00316aa
   0x656300: ldr      x25, [x20, #8] ; 990640f9
   0x656304: str      q0, [sp] ; e003803d
   0x656308: ldr      x8, [x22] ; c80240f9
   0x65630C: ldr      x9, [x8, #0x410] ; 090942f9
   0x656310: sub      x8, x29, #0xa8 ; a8a302d1
   0x656314: blr      x9 ; 20013fd6
   0x656318: ldr      x8, [x22] ; c80240f9
   0x65631C: mov      x0, x22 ; e00316aa
   0x656320: ldr      x8, [x8, #0xb8] ; 085d40f9
   0x656324: blr      x8 ; 00013fd6
   0x656328: cbz      w0, #0x656370 ; 40020034
   0x65632C: mov      w23, #1 ; 37008052
   0x656330: ldr      x8, [x22] ; c80240f9
   0x656334: mov      x0, x22 ; e00316aa
   0x656338: mov      w1, w23 ; e103172a
   0x65633C: ldr      x9, [x8, #0x400] ; 090142f9
   0x656340: add      x8, sp, #0x110 ; e8430491
   0x656344: blr      x9 ; 20013fd6
   0x656348: sub      x0, x29, #0xa8 ; a0a302d1
   0x65634C: add      x1, sp, #0x110 ; e1430491
   0x656350: bl       #0x656c00 ; 2c020094
   0x656354: ldr      x8, [x22] ; c80240f9
   0x656358: mov      x0, x22 ; e00316aa
   0x65635C: add      w23, w23, #1 ; f7060011
   0x656360: ldr      x8, [x8, #0xb8] ; 085d40f9
   0x656364: blr      x8 ; 00013fd6
   0x656368: cmp      w23, w0 ; ff02006b
   0x65636C: b.ls     #0x656330 ; 29feff54
   0x656370: mov      x23, xzr ; f7031faa
   0x656374: mov      x24, xzr ; f8031faa
   0x656378: mov      x26, sp ; fa030091
   0x65637C: mov      x27, #0x3fffffffffffffff ; 1b00f892
   0x656380: stp      xzr, xzr, [sp, #0x110] ; ff7f11a9
   0x656384: mov      x28, #0x7fffffffffffffff ; 1c00f092
   0x656388: stp      xzr, x25, [sp, #0x120] ; ff6712a9
   0x65638C: ldr      w25, [x26, x24, lsl #2] ; 597b78b8
   0x656390: tbnz     w25, #0x1f, #0x656aa0 ; 9938f837
   0x656394: mov      w0, w25 ; e003192a
   0x656398: bl       #0x41ea50 ; ae21f797
   0x65639C: tbnz     w0, #0, #0x6569b8 ; e0300037
   0x6563A0: ldr      x8, [x22] ; c80240f9
   0x6563A4: mov      x0, x22 ; e00316aa
   0x6563A8: mov      w1, w24 ; e103182a
   0x6563AC: mov      w2, wzr ; e2031f2a
   0x6563B0: ldr      x8, [x8, #0x110] ; 088940f9
   0x6563B4: blr      x8 ; 00013fd6
   0x6563B8: ldr      x8, [sp, #0x120] ; e89340f9
   0x6563BC: cmp      x23, x8 ; ff0208eb
   0x6563C0: b.ne     #0x656454 ; a1040054
   0x6563C4: ldr      x8, [sp, #0x110] ; e88b40f9
   0x6563C8: sub      x23, x23, x8 ; f70208cb
   0x6563CC: adds     x8, x23, #1 ; e80600b1
   0x6563D0: b.mi     #0x656b98 ; 443e0054
   0x6563D4: lsl      x9, x23, #1 ; e9fa7fd3
   0x6563D8: cmp      x9, x8 ; 3f0108eb
   0x6563DC: csel     x8, x9, x8, hi ; 2881889a
   0x6563E0: cmp      x23, x27 ; ff021beb
   0x6563E4: csel     x25, x8, x28, lo ; 19319c9a
   0x6563E8: cbz      x25, #0x656b90 ; 593d00b4
   0x6563EC: ldr      x0, [sp, #0x128] ; e09740f9
   0x6563F0: mov      x1, x25 ; e10319aa
   0x6563F4: mov      w2, #1 ; 22008052
   0x6563F8: bl       #0x5388 ; e4bbe697
   0x6563FC: add      x8, x0, x23 ; 0800178b
   0x656400: mov      x23, x8 ; f70308aa
   0x656404: strb     w24, [x23], #1 ; f8160038
   0x656408: ldp      x9, x1, [sp, #0x110] ; e90751a9
   0x65640C: cmp      x1, x9 ; 3f0009eb
   0x656410: b.ne     #0x65643c ; 61010054
   0x656414: stp      x8, x23, [sp, #0x110] ; e85f11a9
   0x656418: ldr      x8, [sp, #0x120] ; e89340f9
   0x65641C: add      x9, x0, x25 ; 0900198b
   0x656420: str      x9, [sp, #0x120] ; e99300f9
   0x656424: cbz      x1, #0x65645c ; c10100b4
   0x656428: ldr      x0, [sp, #0x128] ; e09740f9
   0x65642C: sub      x2, x8, x1 ; 020101cb
   0x656430: mov      w3, #1 ; 23008052
   0x656434: bl       #0xf308 ; b5e3e697
   0x656438: b        #0x65645c ; 09000014
   0x65643C: ldrb     w10, [x1, #-1]! ; 2afc5f38
   0x656440: cmp      x1, x9 ; 3f0009eb
   0x656444: strb     w10, [x8, #-1]! ; 0afd1f38
   0x656448: b.ne     #0x65643c ; a1ffff54
   0x65644C: ldr      x1, [sp, #0x110] ; e18b40f9
   0x656450: b        #0x656414 ; f1ffff17
   0x656454: strb     w24, [x23], #1 ; f8160038
   0x656458: str      x23, [sp, #0x118] ; f78f00f9
   0x65645C: add      x24, x24, #1 ; 18070091
   0x656460: cmp      x24, #4 ; 1f1300f1
   0x656464: b.ne     #0x65638c ; 41f9ff54
   0x656468: ldr      x26, [sp, #0x110] ; fa8b40f9
   0x65646C: cmp      x26, x23 ; 5f0317eb
   0x656470: b.eq     #0x656a4c ; e02e0054
   0x656474: sub      x0, x29, #0xa8 ; a0a302d1
   0x656478: bl       #0x656bd4 ; d7010094
   0x65647C: mov      w24, w0 ; f803002a
   0x656480: mov      x27, xzr ; fb031faa
   0x656484: sub      x28, x23, x26 ; fc021acb
   0x656488: cmp      w24, #1 ; 1f070071
   0x65648C: b.lt     #0x656a48 ; eb2d0054
   0x656490: sub      w23, w24, #1 ; 17070051
   0x656494: sub      x0, x29, #0xa8 ; a0a302d1
   0x656498: mov      w1, w23 ; e103172a
   0x65649C: bl       #0x656bdc ; d0010094
   0x6564A0: mov      w25, w0 ; f903002a
   0x6564A4: bl       #0x41ea50 ; 6b21f797
   0x6564A8: tbz      w0, #0, #0x656a38 ; 802c0036
   0x6564AC: ldr      x8, [x22] ; c80240f9
   0x6564B0: mov      x0, x22 ; e00316aa
   0x6564B4: mov      w1, w25 ; e103192a
   0x6564B8: ldr      x8, [x8, #0x368] ; 08b541f9
   0x6564BC: blr      x8 ; 00013fd6
   0x6564C0: tbnz     w0, #0, #0x656a38 ; c02b0037
~~~

