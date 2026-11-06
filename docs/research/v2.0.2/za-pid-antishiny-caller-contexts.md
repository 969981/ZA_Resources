# Z-A v2.0.2 AntiShiny and PID generator callers exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 9
- Instruction window: 0x280 bytes before and 0x120 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0x55BD9C (word 0x94240513)

- ELF file offset: 0x55C7E4; opcode: BL; mask: to shiny_xor_check (0xE5D1E8)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x55BB1C: ldxr     w12, [x11] ; 6c7d5f88
   0x55BB20: sub      w13, w12, #0x400 ; 8d011051
   0x55BB24: stlxr    w14, w13, [x11] ; 6dfd0e88
   0x55BB28: cbnz     w14, #0x55bb1c ; aeffff35
   0x55BB2C: and      w11, w12, #0xfffffc00 ; 8b551612
   0x55BB30: cmp      w11, #0x400 ; 7f011071
   0x55BB34: b.ne     #0x55b6a4 ; 81dbff54
   0x55BB38: and      x8, x8, #0x3fc ; 081d7e92
   0x55BB3C: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x55BB40: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x55BB44: lsr      x1, x8, #2 ; 01fd42d3
   0x55BB48: bl       #0x95a40 ; bee7ec97
   0x55BB4C: b        #0x55b6a4 ; d6feff17
   0x55BB50: cmp      x10, #1 ; 5f0500f1
   0x55BB54: b.ne     #0x55b50c ; c1cdff54
   0x55BB58: cmp      w8, #1 ; 1f050071
   0x55BB5C: b.ne     #0x55bb90 ; a1010054
   0x55BB60: ldr      x0, [x20] ; 800240f9
   0x55BB64: cbnz     x0, #0x55b504 ; 00cdffb5
   0x55BB68: stp      xzr, xzr, [sp, #8] ; ffff00a9
   0x55BB6C: mov      w8, #1 ; 28008052
   0x55BB70: str      xzr, [sp, #0x18] ; ff0f00f9
   0x55BB74: adrp     x9, #0x3cee000 ; 89bc01f0
   0x55BB78: add      x9, x9, #0x50 ; 29410191
   0x55BB7C: add      x0, x29, #0x1f ; a07f0091
   0x55BB80: ldr      x8, [x9, w8, uxtw #3] ; 285968f8
   0x55BB84: mov      x1, x20 ; e10314aa
   0x55BB88: blr      x8 ; 00013fd6
   0x55BB8C: b        #0x55bb9c ; 04000014
   0x55BB90: bl       #0x3707f0 ; 1853f897
   0x55BB94: cmn      w8, #1 ; 1f050031
   0x55BB98: b.ne     #0x55bb74 ; e1feff54
   0x55BB9C: ldur     q0, [sp, #8] ; e083c03c
   0x55BBA0: str      wzr, [x19, #0x7e0] ; 7fe207b9
   0x55BBA4: ldr      x8, [sp, #0x18] ; e80f40f9
   0x55BBA8: str      x8, [x20, #0x10] ; 880a00f9
   0x55BBAC: str      q0, [x20] ; 8002803d
   0x55BBB0: b        #0x55b520 ; 5cfeff17
   0x55BBB4: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BBB8: str      x19, [sp, #0x10] ; f30b00f9
   0x55BBBC: mov      x29, sp ; fd030091
   0x55BBC0: mov      x19, x0 ; f30300aa
   0x55BBC4: bl       #0xc23760 ; e71e1b94
   0x55BBC8: add      x0, x19, #0x70 ; 60c20191
   0x55BBCC: bl       #0x8282c8 ; bf310b94
   0x55BBD0: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BBD4: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BBD8: ldr      x19, [sp, #0x10] ; f30b40f9
   0x55BBDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BBE0: ret       ; c0035fd6
   0x55BBE4: adrp     x8, #0x610f000 ; a8dd0290
   0x55BBE8: add      x8, x8, #0x800 ; 08012091
   0x55BBEC: ldr      w8, [x8, #0x200] ; 080142b9
   0x55BBF0: dmb      ishld ; bf3903d5
   0x55BBF4: cbz      w8, #0x55bc2c ; c8010034
   0x55BBF8: sub      sp, sp, #0x20 ; ff8300d1
   0x55BBFC: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x55BC00: add      x29, sp, #0x10 ; fd430091
   0x55BC04: add      x0, sp, #4 ; e0130091
   0x55BC08: bl       #0x82383c ; 0d1f0b94
   0x55BC0C: mov      w8, #0xb ; 68018052
   0x55BC10: adrp     x0, #0x3ec3000 ; 40cb0190
   0x55BC14: str      w8, [sp, #4] ; e80700b9
   0x55BC18: add      x1, sp, #4 ; e1130091
   0x55BC1C: ldr      x0, [x0, #0x7c8] ; 00e443f9
   0x55BC20: bl       #0x827f2c ; c3300b94
   0x55BC24: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x55BC28: add      sp, sp, #0x20 ; ff830091
   0x55BC2C: ret       ; c0035fd6
   0x55BC30: stp      x29, x30, [sp, #-0x30]! ; fd7bbda9
   0x55BC34: str      x21, [sp, #0x10] ; f50b00f9
   0x55BC38: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x55BC3C: mov      x29, sp ; fd030091
   0x55BC40: adrp     x8, #0x3ec5000 ; 48cb01d0
   0x55BC44: mov      w20, w1 ; f403012a
   0x55BC48: ldr      x8, [x8, #0xaa8] ; 085545f9
   0x55BC4C: mov      x19, x0 ; f30300aa
   0x55BC50: ldr      w8, [x8, #0x80] ; 088140b9
   0x55BC54: dmb      ishld ; bf3903d5
   0x55BC58: cbz      w8, #0x55bc8c ; a8010034
   0x55BC5C: add      x8, x29, #0x18 ; a8630091
   0x55BC60: bl       #0x61eb84 ; c90b0394
   0x55BC64: ldr      x21, [x29, #0x18] ; b50f40f9
   0x55BC68: cbz      x21, #0x55bc84 ; f50000b4
   0x55BC6C: adrp     x0, #0x6128000 ; 60de02b0
   0x55BC70: add      x0, x0, #0xf00 ; 00003c91
   0x55BC74: bl       #0xd0a7d0 ; d7ba1e94
   0x55BC78: and      w8, w0, #0xffff ; 083c0012
   0x55BC7C: ucvtf    d0, w8 ; 0001631e
   0x55BC80: str      d0, [x21, #0x40] ; a02200fd
   0x55BC84: add      x0, x29, #0x18 ; a0630091
   0x55BC88: bl       #0x798b70 ; baf30894
   0x55BC8C: add      x0, x19, #0x70 ; 60c20191
   0x55BC90: bl       #0x8282c8 ; 8e310b94
   0x55BC94: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BC98: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BC9C: tbz      w20, #0, #0x55bcb4 ; d4000036
   0x55BCA0: ldr      x8, [x19, #0x30] ; 681a40f9
   0x55BCA4: str      x8, [x19, #0x38] ; 681e00f9
   0x55BCA8: ldr      x8, [x19, #0x50] ; 682a40f9
   0x55BCAC: str      x8, [x19, #0x58] ; 682e00f9
   0x55BCB0: b        #0x55bcbc ; 03000014
   0x55BCB4: mov      x0, x19 ; e00313aa
   0x55BCB8: bl       #0x2aa6cb0 ; fe2b9594
   0x55BCBC: bl       #0xc23760 ; a91e1b94
   0x55BCC0: bl       #0x48d4bc ; ffc5fc97
   0x55BCC4: str      wzr, [x19, #0xc8] ; 7fca00b9
   0x55BCC8: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x55BCCC: ldr      x21, [sp, #0x10] ; f50b40f9
   0x55BCD0: ldp      x29, x30, [sp], #0x30 ; fd7bc3a8
   0x55BCD4: ret       ; c0035fd6
   0x55BCD8: ldr      x0, [x0, #0x18] ; 000c40f9
   0x55BCDC: cbnz     x0, #0x55bce4 ; 400000b5
   0x55BCE0: ret       ; c0035fd6
   0x55BCE4: ldr      w8, [x0, #8] ; 080840b9
   0x55BCE8: tst      w8, #3 ; 1f050072
   0x55BCEC: b.eq     #0x55bce0 ; a0ffff54
   0x55BCF0: ldr      w8, [x0, #8] ; 080840b9
   0x55BCF4: add      x11, x0, #8 ; 0b200091
   0x55BCF8: ldr      w9, [x0, #0xc] ; 090c40b9
   0x55BCFC: ldrb     w10, [x0, #0x10] ; 0a404039
   0x55BD00: ldr      x2, [x0] ; 020040f9
   0x55BD04: ldxr     w12, [x11] ; 6c7d5f88
   0x55BD08: sub      w13, w12, #0x400 ; 8d011051
   0x55BD0C: stlxr    w14, w13, [x11] ; 6dfd0e88
   0x55BD10: cbnz     w14, #0x55bd04 ; aeffff35
   0x55BD14: and      w11, w12, #0xfffffc00 ; 8b551612
   0x55BD18: cmp      w11, #0x400 ; 7f011071
   0x55BD1C: b.ne     #0x55bce0 ; 21feff54
   0x55BD20: and      x8, x8, #0x3fc ; 081d7e92
   0x55BD24: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x55BD28: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x55BD2C: lsr      x1, x8, #2 ; 01fd42d3
   0x55BD30: b        #0x95a40 ; 44e7ec17
   0x55BD34: ldr      x0, [x0, #0x50] ; 002840f9
   0x55BD38: b        #0x55bd3c ; 01000014
   0x55BD3C: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BD40: stp      x20, x19, [sp, #0x10] ; f44f01a9
   0x55BD44: mov      x29, sp ; fd030091
   0x55BD48: mov      x19, x0 ; f30300aa
   0x55BD4C: bl       #0x3f0784 ; 8e52fa97
   0x55BD50: ldrb     w8, [x0, #0x380] ; 08004e39
   0x55BD54: cbnz     w8, #0x55bd80 ; 68010035
   0x55BD58: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD5C: bl       #0xe483b4 ; 96b12394
   0x55BD60: tbnz     w0, #0, #0x55bd80 ; 00010037
   0x55BD64: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD68: bl       #0xe4c950 ; fac22394
   0x55BD6C: mov      w20, w0 ; f403002a
   0x55BD70: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD74: bl       #0xe485f0 ; 1fb22394
   0x55BD78: tbnz     w20, #0, #0x55bdd8 ; 14030037
   0x55BD7C: tbnz     w0, #0, #0x55bdd8 ; e0020037
   0x55BD80: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD84: bl       #0xe49d50 ; f3b72394
   0x55BD88: mov      w20, w0 ; f403002a
   0x55BD8C: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD90: bl       #0xe4dbe0 ; 94c72394
   0x55BD94: mov      w1, w0 ; e103002a
   0x55BD98: mov      w0, w20 ; e003142a
>> 0x55BD9C: bl       #0xe5d1e8 ; 13052494
   0x55BDA0: tbz      w0, #0, #0x55bdd8 ; c0010036
   0x55BDA4: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDA8: bl       #0xe49d50 ; eab72394
   0x55BDAC: mov      w20, w0 ; f403002a
   0x55BDB0: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDB4: bl       #0xe4dbe0 ; 8bc72394
   0x55BDB8: mov      w1, w0 ; e103002a
   0x55BDBC: mov      w0, w20 ; e003142a
   0x55BDC0: bl       #0xe5d200 ; 10052494
   0x55BDC4: mov      w1, w0 ; e103002a
   0x55BDC8: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDCC: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDD0: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BDD4: b        #0xe57350 ; 5fed2314
   0x55BDD8: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BDE0: ret       ; c0035fd6
   0x55BDE4: udf      #0 ; 00000000
   0x55BDE8: udf      #0 ; 00000000
   0x55BDEC: udf      #0 ; 00000000
   0x55BDF0: str      d8, [sp, #-0x40]! ; e80f1cfc
   0x55BDF4: stp      x29, x30, [sp, #8] ; fdfb00a9
   0x55BDF8: str      x23, [sp, #0x18] ; f70f00f9
   0x55BDFC: stp      x22, x21, [sp, #0x20] ; f65702a9
   0x55BE00: stp      x20, x19, [sp, #0x30] ; f44f03a9
   0x55BE04: add      x29, sp, #8 ; fd230091
   0x55BE08: ldrb     w8, [x0, #0x122] ; 08884439
   0x55BE0C: fmov     s8, s0 ; 0840201e
   0x55BE10: mrs      x9, tpidr_el0 ; 49d03bd5
   0x55BE14: ubfx     w22, w9, #0xd, #7 ; 364d0d53
   0x55BE18: mov      x19, x0 ; f30300aa
   0x55BE1C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE20: ccmp     w8, w22, #0, ne ; 0011567a
   0x55BE24: b.eq     #0x55bf28 ; 20080054
   0x55BE28: add      x20, x19, #0x120 ; 74820491
   0x55BE2C: add      x21, x19, #0x122 ; 758a0491
   0x55BE30: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE34: cmp      w8, #0x5f ; 1f7d0171
   0x55BE38: b.ne     #0x55be48 ; 81000054
   0x55BE3C: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE40: cbnz     w8, #0x55be30 ; 88ffff35
   0x55BE44: b        #0x55beac ; 1a000014
   0x55BE48: add      x23, x19, #0x123 ; 778e0491
   0x55BE4C: clrex     ; 5f3f03d5
   0x55BE50: ldxrb    w8, [x23] ; e87e5f08
   0x55BE54: add      w8, w8, #1 ; 08050011
   0x55BE58: stxrb    w9, w8, [x23] ; e87e0908
   0x55BE5C: cbnz     w9, #0x55be50 ; a9ffff35
   0x55BE60: dmb      ish ; bf3b03d5
   0x55BE64: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE68: cmp      w8, #0x5f ; 1f7d0171
   0x55BE6C: b.ne     #0x55be7c ; 81000054
   0x55BE70: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE74: cbnz     w8, #0x55be64 ; 88ffff35
   0x55BE78: b        #0x55be9c ; 09000014
   0x55BE7C: mov      x0, x20 ; e00314aa
   0x55BE80: clrex     ; 5f3f03d5
   0x55BE84: bl       #0x3160670 ; fb11b094
   0x55BE88: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE8C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE90: b.ne     #0x55be7c ; 61ffff54
   0x55BE94: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE98: cbnz     w8, #0x55be88 ; 88ffff35
   0x55BE9C: ldxrb    w8, [x23] ; e87e5f08
   0x55BEA0: sub      w8, w8, #1 ; 08050051
   0x55BEA4: stxrb    w9, w8, [x23] ; e87e0908
   0x55BEA8: cbnz     w9, #0x55be9c ; a9ffff35
   0x55BEAC: mov      x0, x19 ; e00313aa
   0x55BEB0: bl       #0x3b50 ; 289fea97
   0x55BEB4: ldrh     w8, [x0] ; 08004079
   0x55BEB8: mov      w9, #0x5f ; e90b8052
   0x55BEBC: ldxrb    wzr, [x21] ; bf7e5f08
~~~

## Static PC 0x55BDC0 (word 0x94240510)

- ELF file offset: 0x55C808; opcode: BL; mask: to pid_anti_shiny_if_needed_a (0xE5D200)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x55BB40: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x55BB44: lsr      x1, x8, #2 ; 01fd42d3
   0x55BB48: bl       #0x95a40 ; bee7ec97
   0x55BB4C: b        #0x55b6a4 ; d6feff17
   0x55BB50: cmp      x10, #1 ; 5f0500f1
   0x55BB54: b.ne     #0x55b50c ; c1cdff54
   0x55BB58: cmp      w8, #1 ; 1f050071
   0x55BB5C: b.ne     #0x55bb90 ; a1010054
   0x55BB60: ldr      x0, [x20] ; 800240f9
   0x55BB64: cbnz     x0, #0x55b504 ; 00cdffb5
   0x55BB68: stp      xzr, xzr, [sp, #8] ; ffff00a9
   0x55BB6C: mov      w8, #1 ; 28008052
   0x55BB70: str      xzr, [sp, #0x18] ; ff0f00f9
   0x55BB74: adrp     x9, #0x3cee000 ; 89bc01f0
   0x55BB78: add      x9, x9, #0x50 ; 29410191
   0x55BB7C: add      x0, x29, #0x1f ; a07f0091
   0x55BB80: ldr      x8, [x9, w8, uxtw #3] ; 285968f8
   0x55BB84: mov      x1, x20 ; e10314aa
   0x55BB88: blr      x8 ; 00013fd6
   0x55BB8C: b        #0x55bb9c ; 04000014
   0x55BB90: bl       #0x3707f0 ; 1853f897
   0x55BB94: cmn      w8, #1 ; 1f050031
   0x55BB98: b.ne     #0x55bb74 ; e1feff54
   0x55BB9C: ldur     q0, [sp, #8] ; e083c03c
   0x55BBA0: str      wzr, [x19, #0x7e0] ; 7fe207b9
   0x55BBA4: ldr      x8, [sp, #0x18] ; e80f40f9
   0x55BBA8: str      x8, [x20, #0x10] ; 880a00f9
   0x55BBAC: str      q0, [x20] ; 8002803d
   0x55BBB0: b        #0x55b520 ; 5cfeff17
   0x55BBB4: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BBB8: str      x19, [sp, #0x10] ; f30b00f9
   0x55BBBC: mov      x29, sp ; fd030091
   0x55BBC0: mov      x19, x0 ; f30300aa
   0x55BBC4: bl       #0xc23760 ; e71e1b94
   0x55BBC8: add      x0, x19, #0x70 ; 60c20191
   0x55BBCC: bl       #0x8282c8 ; bf310b94
   0x55BBD0: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BBD4: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BBD8: ldr      x19, [sp, #0x10] ; f30b40f9
   0x55BBDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BBE0: ret       ; c0035fd6
   0x55BBE4: adrp     x8, #0x610f000 ; a8dd0290
   0x55BBE8: add      x8, x8, #0x800 ; 08012091
   0x55BBEC: ldr      w8, [x8, #0x200] ; 080142b9
   0x55BBF0: dmb      ishld ; bf3903d5
   0x55BBF4: cbz      w8, #0x55bc2c ; c8010034
   0x55BBF8: sub      sp, sp, #0x20 ; ff8300d1
   0x55BBFC: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x55BC00: add      x29, sp, #0x10 ; fd430091
   0x55BC04: add      x0, sp, #4 ; e0130091
   0x55BC08: bl       #0x82383c ; 0d1f0b94
   0x55BC0C: mov      w8, #0xb ; 68018052
   0x55BC10: adrp     x0, #0x3ec3000 ; 40cb0190
   0x55BC14: str      w8, [sp, #4] ; e80700b9
   0x55BC18: add      x1, sp, #4 ; e1130091
   0x55BC1C: ldr      x0, [x0, #0x7c8] ; 00e443f9
   0x55BC20: bl       #0x827f2c ; c3300b94
   0x55BC24: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x55BC28: add      sp, sp, #0x20 ; ff830091
   0x55BC2C: ret       ; c0035fd6
   0x55BC30: stp      x29, x30, [sp, #-0x30]! ; fd7bbda9
   0x55BC34: str      x21, [sp, #0x10] ; f50b00f9
   0x55BC38: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x55BC3C: mov      x29, sp ; fd030091
   0x55BC40: adrp     x8, #0x3ec5000 ; 48cb01d0
   0x55BC44: mov      w20, w1 ; f403012a
   0x55BC48: ldr      x8, [x8, #0xaa8] ; 085545f9
   0x55BC4C: mov      x19, x0 ; f30300aa
   0x55BC50: ldr      w8, [x8, #0x80] ; 088140b9
   0x55BC54: dmb      ishld ; bf3903d5
   0x55BC58: cbz      w8, #0x55bc8c ; a8010034
   0x55BC5C: add      x8, x29, #0x18 ; a8630091
   0x55BC60: bl       #0x61eb84 ; c90b0394
   0x55BC64: ldr      x21, [x29, #0x18] ; b50f40f9
   0x55BC68: cbz      x21, #0x55bc84 ; f50000b4
   0x55BC6C: adrp     x0, #0x6128000 ; 60de02b0
   0x55BC70: add      x0, x0, #0xf00 ; 00003c91
   0x55BC74: bl       #0xd0a7d0 ; d7ba1e94
   0x55BC78: and      w8, w0, #0xffff ; 083c0012
   0x55BC7C: ucvtf    d0, w8 ; 0001631e
   0x55BC80: str      d0, [x21, #0x40] ; a02200fd
   0x55BC84: add      x0, x29, #0x18 ; a0630091
   0x55BC88: bl       #0x798b70 ; baf30894
   0x55BC8C: add      x0, x19, #0x70 ; 60c20191
   0x55BC90: bl       #0x8282c8 ; 8e310b94
   0x55BC94: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BC98: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BC9C: tbz      w20, #0, #0x55bcb4 ; d4000036
   0x55BCA0: ldr      x8, [x19, #0x30] ; 681a40f9
   0x55BCA4: str      x8, [x19, #0x38] ; 681e00f9
   0x55BCA8: ldr      x8, [x19, #0x50] ; 682a40f9
   0x55BCAC: str      x8, [x19, #0x58] ; 682e00f9
   0x55BCB0: b        #0x55bcbc ; 03000014
   0x55BCB4: mov      x0, x19 ; e00313aa
   0x55BCB8: bl       #0x2aa6cb0 ; fe2b9594
   0x55BCBC: bl       #0xc23760 ; a91e1b94
   0x55BCC0: bl       #0x48d4bc ; ffc5fc97
   0x55BCC4: str      wzr, [x19, #0xc8] ; 7fca00b9
   0x55BCC8: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x55BCCC: ldr      x21, [sp, #0x10] ; f50b40f9
   0x55BCD0: ldp      x29, x30, [sp], #0x30 ; fd7bc3a8
   0x55BCD4: ret       ; c0035fd6
   0x55BCD8: ldr      x0, [x0, #0x18] ; 000c40f9
   0x55BCDC: cbnz     x0, #0x55bce4 ; 400000b5
   0x55BCE0: ret       ; c0035fd6
   0x55BCE4: ldr      w8, [x0, #8] ; 080840b9
   0x55BCE8: tst      w8, #3 ; 1f050072
   0x55BCEC: b.eq     #0x55bce0 ; a0ffff54
   0x55BCF0: ldr      w8, [x0, #8] ; 080840b9
   0x55BCF4: add      x11, x0, #8 ; 0b200091
   0x55BCF8: ldr      w9, [x0, #0xc] ; 090c40b9
   0x55BCFC: ldrb     w10, [x0, #0x10] ; 0a404039
   0x55BD00: ldr      x2, [x0] ; 020040f9
   0x55BD04: ldxr     w12, [x11] ; 6c7d5f88
   0x55BD08: sub      w13, w12, #0x400 ; 8d011051
   0x55BD0C: stlxr    w14, w13, [x11] ; 6dfd0e88
   0x55BD10: cbnz     w14, #0x55bd04 ; aeffff35
   0x55BD14: and      w11, w12, #0xfffffc00 ; 8b551612
   0x55BD18: cmp      w11, #0x400 ; 7f011071
   0x55BD1C: b.ne     #0x55bce0 ; 21feff54
   0x55BD20: and      x8, x8, #0x3fc ; 081d7e92
   0x55BD24: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x55BD28: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x55BD2C: lsr      x1, x8, #2 ; 01fd42d3
   0x55BD30: b        #0x95a40 ; 44e7ec17
   0x55BD34: ldr      x0, [x0, #0x50] ; 002840f9
   0x55BD38: b        #0x55bd3c ; 01000014
   0x55BD3C: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BD40: stp      x20, x19, [sp, #0x10] ; f44f01a9
   0x55BD44: mov      x29, sp ; fd030091
   0x55BD48: mov      x19, x0 ; f30300aa
   0x55BD4C: bl       #0x3f0784 ; 8e52fa97
   0x55BD50: ldrb     w8, [x0, #0x380] ; 08004e39
   0x55BD54: cbnz     w8, #0x55bd80 ; 68010035
   0x55BD58: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD5C: bl       #0xe483b4 ; 96b12394
   0x55BD60: tbnz     w0, #0, #0x55bd80 ; 00010037
   0x55BD64: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD68: bl       #0xe4c950 ; fac22394
   0x55BD6C: mov      w20, w0 ; f403002a
   0x55BD70: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD74: bl       #0xe485f0 ; 1fb22394
   0x55BD78: tbnz     w20, #0, #0x55bdd8 ; 14030037
   0x55BD7C: tbnz     w0, #0, #0x55bdd8 ; e0020037
   0x55BD80: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD84: bl       #0xe49d50 ; f3b72394
   0x55BD88: mov      w20, w0 ; f403002a
   0x55BD8C: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD90: bl       #0xe4dbe0 ; 94c72394
   0x55BD94: mov      w1, w0 ; e103002a
   0x55BD98: mov      w0, w20 ; e003142a
   0x55BD9C: bl       #0xe5d1e8 ; 13052494
   0x55BDA0: tbz      w0, #0, #0x55bdd8 ; c0010036
   0x55BDA4: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDA8: bl       #0xe49d50 ; eab72394
   0x55BDAC: mov      w20, w0 ; f403002a
   0x55BDB0: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDB4: bl       #0xe4dbe0 ; 8bc72394
   0x55BDB8: mov      w1, w0 ; e103002a
   0x55BDBC: mov      w0, w20 ; e003142a
>> 0x55BDC0: bl       #0xe5d200 ; 10052494
   0x55BDC4: mov      w1, w0 ; e103002a
   0x55BDC8: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDCC: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDD0: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BDD4: b        #0xe57350 ; 5fed2314
   0x55BDD8: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BDE0: ret       ; c0035fd6
   0x55BDE4: udf      #0 ; 00000000
   0x55BDE8: udf      #0 ; 00000000
   0x55BDEC: udf      #0 ; 00000000
   0x55BDF0: str      d8, [sp, #-0x40]! ; e80f1cfc
   0x55BDF4: stp      x29, x30, [sp, #8] ; fdfb00a9
   0x55BDF8: str      x23, [sp, #0x18] ; f70f00f9
   0x55BDFC: stp      x22, x21, [sp, #0x20] ; f65702a9
   0x55BE00: stp      x20, x19, [sp, #0x30] ; f44f03a9
   0x55BE04: add      x29, sp, #8 ; fd230091
   0x55BE08: ldrb     w8, [x0, #0x122] ; 08884439
   0x55BE0C: fmov     s8, s0 ; 0840201e
   0x55BE10: mrs      x9, tpidr_el0 ; 49d03bd5
   0x55BE14: ubfx     w22, w9, #0xd, #7 ; 364d0d53
   0x55BE18: mov      x19, x0 ; f30300aa
   0x55BE1C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE20: ccmp     w8, w22, #0, ne ; 0011567a
   0x55BE24: b.eq     #0x55bf28 ; 20080054
   0x55BE28: add      x20, x19, #0x120 ; 74820491
   0x55BE2C: add      x21, x19, #0x122 ; 758a0491
   0x55BE30: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE34: cmp      w8, #0x5f ; 1f7d0171
   0x55BE38: b.ne     #0x55be48 ; 81000054
   0x55BE3C: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE40: cbnz     w8, #0x55be30 ; 88ffff35
   0x55BE44: b        #0x55beac ; 1a000014
   0x55BE48: add      x23, x19, #0x123 ; 778e0491
   0x55BE4C: clrex     ; 5f3f03d5
   0x55BE50: ldxrb    w8, [x23] ; e87e5f08
   0x55BE54: add      w8, w8, #1 ; 08050011
   0x55BE58: stxrb    w9, w8, [x23] ; e87e0908
   0x55BE5C: cbnz     w9, #0x55be50 ; a9ffff35
   0x55BE60: dmb      ish ; bf3b03d5
   0x55BE64: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE68: cmp      w8, #0x5f ; 1f7d0171
   0x55BE6C: b.ne     #0x55be7c ; 81000054
   0x55BE70: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE74: cbnz     w8, #0x55be64 ; 88ffff35
   0x55BE78: b        #0x55be9c ; 09000014
   0x55BE7C: mov      x0, x20 ; e00314aa
   0x55BE80: clrex     ; 5f3f03d5
   0x55BE84: bl       #0x3160670 ; fb11b094
   0x55BE88: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE8C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE90: b.ne     #0x55be7c ; 61ffff54
   0x55BE94: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE98: cbnz     w8, #0x55be88 ; 88ffff35
   0x55BE9C: ldxrb    w8, [x23] ; e87e5f08
   0x55BEA0: sub      w8, w8, #1 ; 08050051
   0x55BEA4: stxrb    w9, w8, [x23] ; e87e0908
   0x55BEA8: cbnz     w9, #0x55be9c ; a9ffff35
   0x55BEAC: mov      x0, x19 ; e00313aa
   0x55BEB0: bl       #0x3b50 ; 289fea97
   0x55BEB4: ldrh     w8, [x0] ; 08004079
   0x55BEB8: mov      w9, #0x5f ; e90b8052
   0x55BEBC: ldxrb    wzr, [x21] ; bf7e5f08
   0x55BEC0: stlxrb   w10, w9, [x21] ; a9fe0a08
   0x55BEC4: cbnz     w10, #0x55bebc ; caffff35
   0x55BEC8: dmb      ish ; bf3b03d5
   0x55BECC: lsr      w21, w8, #8 ; 157d0853
   0x55BED0: ldrb     w8, [x19, #0x123] ; 688e4439
   0x55BED4: cbnz     w8, #0x55bf54 ; 08040035
   0x55BED8: and      w8, w21, #7 ; a80a0012
   0x55BEDC: cmp      w8, #3 ; 1f0d0071
   0x55BEE0: b.ne     #0x55bf3c ; e1020054
~~~

## Static PC 0x55BDD4 (word 0x1423ED5F)

- ELF file offset: 0x55C81C; opcode: B; mask: to pid_set (0xE57350)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x55BB54: b.ne     #0x55b50c ; c1cdff54
   0x55BB58: cmp      w8, #1 ; 1f050071
   0x55BB5C: b.ne     #0x55bb90 ; a1010054
   0x55BB60: ldr      x0, [x20] ; 800240f9
   0x55BB64: cbnz     x0, #0x55b504 ; 00cdffb5
   0x55BB68: stp      xzr, xzr, [sp, #8] ; ffff00a9
   0x55BB6C: mov      w8, #1 ; 28008052
   0x55BB70: str      xzr, [sp, #0x18] ; ff0f00f9
   0x55BB74: adrp     x9, #0x3cee000 ; 89bc01f0
   0x55BB78: add      x9, x9, #0x50 ; 29410191
   0x55BB7C: add      x0, x29, #0x1f ; a07f0091
   0x55BB80: ldr      x8, [x9, w8, uxtw #3] ; 285968f8
   0x55BB84: mov      x1, x20 ; e10314aa
   0x55BB88: blr      x8 ; 00013fd6
   0x55BB8C: b        #0x55bb9c ; 04000014
   0x55BB90: bl       #0x3707f0 ; 1853f897
   0x55BB94: cmn      w8, #1 ; 1f050031
   0x55BB98: b.ne     #0x55bb74 ; e1feff54
   0x55BB9C: ldur     q0, [sp, #8] ; e083c03c
   0x55BBA0: str      wzr, [x19, #0x7e0] ; 7fe207b9
   0x55BBA4: ldr      x8, [sp, #0x18] ; e80f40f9
   0x55BBA8: str      x8, [x20, #0x10] ; 880a00f9
   0x55BBAC: str      q0, [x20] ; 8002803d
   0x55BBB0: b        #0x55b520 ; 5cfeff17
   0x55BBB4: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BBB8: str      x19, [sp, #0x10] ; f30b00f9
   0x55BBBC: mov      x29, sp ; fd030091
   0x55BBC0: mov      x19, x0 ; f30300aa
   0x55BBC4: bl       #0xc23760 ; e71e1b94
   0x55BBC8: add      x0, x19, #0x70 ; 60c20191
   0x55BBCC: bl       #0x8282c8 ; bf310b94
   0x55BBD0: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BBD4: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BBD8: ldr      x19, [sp, #0x10] ; f30b40f9
   0x55BBDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BBE0: ret       ; c0035fd6
   0x55BBE4: adrp     x8, #0x610f000 ; a8dd0290
   0x55BBE8: add      x8, x8, #0x800 ; 08012091
   0x55BBEC: ldr      w8, [x8, #0x200] ; 080142b9
   0x55BBF0: dmb      ishld ; bf3903d5
   0x55BBF4: cbz      w8, #0x55bc2c ; c8010034
   0x55BBF8: sub      sp, sp, #0x20 ; ff8300d1
   0x55BBFC: stp      x29, x30, [sp, #0x10] ; fd7b01a9
   0x55BC00: add      x29, sp, #0x10 ; fd430091
   0x55BC04: add      x0, sp, #4 ; e0130091
   0x55BC08: bl       #0x82383c ; 0d1f0b94
   0x55BC0C: mov      w8, #0xb ; 68018052
   0x55BC10: adrp     x0, #0x3ec3000 ; 40cb0190
   0x55BC14: str      w8, [sp, #4] ; e80700b9
   0x55BC18: add      x1, sp, #4 ; e1130091
   0x55BC1C: ldr      x0, [x0, #0x7c8] ; 00e443f9
   0x55BC20: bl       #0x827f2c ; c3300b94
   0x55BC24: ldp      x29, x30, [sp, #0x10] ; fd7b41a9
   0x55BC28: add      sp, sp, #0x20 ; ff830091
   0x55BC2C: ret       ; c0035fd6
   0x55BC30: stp      x29, x30, [sp, #-0x30]! ; fd7bbda9
   0x55BC34: str      x21, [sp, #0x10] ; f50b00f9
   0x55BC38: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x55BC3C: mov      x29, sp ; fd030091
   0x55BC40: adrp     x8, #0x3ec5000 ; 48cb01d0
   0x55BC44: mov      w20, w1 ; f403012a
   0x55BC48: ldr      x8, [x8, #0xaa8] ; 085545f9
   0x55BC4C: mov      x19, x0 ; f30300aa
   0x55BC50: ldr      w8, [x8, #0x80] ; 088140b9
   0x55BC54: dmb      ishld ; bf3903d5
   0x55BC58: cbz      w8, #0x55bc8c ; a8010034
   0x55BC5C: add      x8, x29, #0x18 ; a8630091
   0x55BC60: bl       #0x61eb84 ; c90b0394
   0x55BC64: ldr      x21, [x29, #0x18] ; b50f40f9
   0x55BC68: cbz      x21, #0x55bc84 ; f50000b4
   0x55BC6C: adrp     x0, #0x6128000 ; 60de02b0
   0x55BC70: add      x0, x0, #0xf00 ; 00003c91
   0x55BC74: bl       #0xd0a7d0 ; d7ba1e94
   0x55BC78: and      w8, w0, #0xffff ; 083c0012
   0x55BC7C: ucvtf    d0, w8 ; 0001631e
   0x55BC80: str      d0, [x21, #0x40] ; a02200fd
   0x55BC84: add      x0, x29, #0x18 ; a0630091
   0x55BC88: bl       #0x798b70 ; baf30894
   0x55BC8C: add      x0, x19, #0x70 ; 60c20191
   0x55BC90: bl       #0x8282c8 ; 8e310b94
   0x55BC94: ldr      x8, [x19, #0xa8] ; 685640f9
   0x55BC98: str      x8, [x19, #0xb0] ; 685a00f9
   0x55BC9C: tbz      w20, #0, #0x55bcb4 ; d4000036
   0x55BCA0: ldr      x8, [x19, #0x30] ; 681a40f9
   0x55BCA4: str      x8, [x19, #0x38] ; 681e00f9
   0x55BCA8: ldr      x8, [x19, #0x50] ; 682a40f9
   0x55BCAC: str      x8, [x19, #0x58] ; 682e00f9
   0x55BCB0: b        #0x55bcbc ; 03000014
   0x55BCB4: mov      x0, x19 ; e00313aa
   0x55BCB8: bl       #0x2aa6cb0 ; fe2b9594
   0x55BCBC: bl       #0xc23760 ; a91e1b94
   0x55BCC0: bl       #0x48d4bc ; ffc5fc97
   0x55BCC4: str      wzr, [x19, #0xc8] ; 7fca00b9
   0x55BCC8: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x55BCCC: ldr      x21, [sp, #0x10] ; f50b40f9
   0x55BCD0: ldp      x29, x30, [sp], #0x30 ; fd7bc3a8
   0x55BCD4: ret       ; c0035fd6
   0x55BCD8: ldr      x0, [x0, #0x18] ; 000c40f9
   0x55BCDC: cbnz     x0, #0x55bce4 ; 400000b5
   0x55BCE0: ret       ; c0035fd6
   0x55BCE4: ldr      w8, [x0, #8] ; 080840b9
   0x55BCE8: tst      w8, #3 ; 1f050072
   0x55BCEC: b.eq     #0x55bce0 ; a0ffff54
   0x55BCF0: ldr      w8, [x0, #8] ; 080840b9
   0x55BCF4: add      x11, x0, #8 ; 0b200091
   0x55BCF8: ldr      w9, [x0, #0xc] ; 090c40b9
   0x55BCFC: ldrb     w10, [x0, #0x10] ; 0a404039
   0x55BD00: ldr      x2, [x0] ; 020040f9
   0x55BD04: ldxr     w12, [x11] ; 6c7d5f88
   0x55BD08: sub      w13, w12, #0x400 ; 8d011051
   0x55BD0C: stlxr    w14, w13, [x11] ; 6dfd0e88
   0x55BD10: cbnz     w14, #0x55bd04 ; aeffff35
   0x55BD14: and      w11, w12, #0xfffffc00 ; 8b551612
   0x55BD18: cmp      w11, #0x400 ; 7f011071
   0x55BD1C: b.ne     #0x55bce0 ; 21feff54
   0x55BD20: and      x8, x8, #0x3fc ; 081d7e92
   0x55BD24: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x55BD28: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x55BD2C: lsr      x1, x8, #2 ; 01fd42d3
   0x55BD30: b        #0x95a40 ; 44e7ec17
   0x55BD34: ldr      x0, [x0, #0x50] ; 002840f9
   0x55BD38: b        #0x55bd3c ; 01000014
   0x55BD3C: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0x55BD40: stp      x20, x19, [sp, #0x10] ; f44f01a9
   0x55BD44: mov      x29, sp ; fd030091
   0x55BD48: mov      x19, x0 ; f30300aa
   0x55BD4C: bl       #0x3f0784 ; 8e52fa97
   0x55BD50: ldrb     w8, [x0, #0x380] ; 08004e39
   0x55BD54: cbnz     w8, #0x55bd80 ; 68010035
   0x55BD58: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD5C: bl       #0xe483b4 ; 96b12394
   0x55BD60: tbnz     w0, #0, #0x55bd80 ; 00010037
   0x55BD64: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD68: bl       #0xe4c950 ; fac22394
   0x55BD6C: mov      w20, w0 ; f403002a
   0x55BD70: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD74: bl       #0xe485f0 ; 1fb22394
   0x55BD78: tbnz     w20, #0, #0x55bdd8 ; 14030037
   0x55BD7C: tbnz     w0, #0, #0x55bdd8 ; e0020037
   0x55BD80: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD84: bl       #0xe49d50 ; f3b72394
   0x55BD88: mov      w20, w0 ; f403002a
   0x55BD8C: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BD90: bl       #0xe4dbe0 ; 94c72394
   0x55BD94: mov      w1, w0 ; e103002a
   0x55BD98: mov      w0, w20 ; e003142a
   0x55BD9C: bl       #0xe5d1e8 ; 13052494
   0x55BDA0: tbz      w0, #0, #0x55bdd8 ; c0010036
   0x55BDA4: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDA8: bl       #0xe49d50 ; eab72394
   0x55BDAC: mov      w20, w0 ; f403002a
   0x55BDB0: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDB4: bl       #0xe4dbe0 ; 8bc72394
   0x55BDB8: mov      w1, w0 ; e103002a
   0x55BDBC: mov      w0, w20 ; e003142a
   0x55BDC0: bl       #0xe5d200 ; 10052494
   0x55BDC4: mov      w1, w0 ; e103002a
   0x55BDC8: ldr      x0, [x19, #0x70] ; 603a40f9
   0x55BDCC: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDD0: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
>> 0x55BDD4: b        #0xe57350 ; 5fed2314
   0x55BDD8: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0x55BDDC: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0x55BDE0: ret       ; c0035fd6
   0x55BDE4: udf      #0 ; 00000000
   0x55BDE8: udf      #0 ; 00000000
   0x55BDEC: udf      #0 ; 00000000
   0x55BDF0: str      d8, [sp, #-0x40]! ; e80f1cfc
   0x55BDF4: stp      x29, x30, [sp, #8] ; fdfb00a9
   0x55BDF8: str      x23, [sp, #0x18] ; f70f00f9
   0x55BDFC: stp      x22, x21, [sp, #0x20] ; f65702a9
   0x55BE00: stp      x20, x19, [sp, #0x30] ; f44f03a9
   0x55BE04: add      x29, sp, #8 ; fd230091
   0x55BE08: ldrb     w8, [x0, #0x122] ; 08884439
   0x55BE0C: fmov     s8, s0 ; 0840201e
   0x55BE10: mrs      x9, tpidr_el0 ; 49d03bd5
   0x55BE14: ubfx     w22, w9, #0xd, #7 ; 364d0d53
   0x55BE18: mov      x19, x0 ; f30300aa
   0x55BE1C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE20: ccmp     w8, w22, #0, ne ; 0011567a
   0x55BE24: b.eq     #0x55bf28 ; 20080054
   0x55BE28: add      x20, x19, #0x120 ; 74820491
   0x55BE2C: add      x21, x19, #0x122 ; 758a0491
   0x55BE30: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE34: cmp      w8, #0x5f ; 1f7d0171
   0x55BE38: b.ne     #0x55be48 ; 81000054
   0x55BE3C: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE40: cbnz     w8, #0x55be30 ; 88ffff35
   0x55BE44: b        #0x55beac ; 1a000014
   0x55BE48: add      x23, x19, #0x123 ; 778e0491
   0x55BE4C: clrex     ; 5f3f03d5
   0x55BE50: ldxrb    w8, [x23] ; e87e5f08
   0x55BE54: add      w8, w8, #1 ; 08050011
   0x55BE58: stxrb    w9, w8, [x23] ; e87e0908
   0x55BE5C: cbnz     w9, #0x55be50 ; a9ffff35
   0x55BE60: dmb      ish ; bf3b03d5
   0x55BE64: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE68: cmp      w8, #0x5f ; 1f7d0171
   0x55BE6C: b.ne     #0x55be7c ; 81000054
   0x55BE70: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE74: cbnz     w8, #0x55be64 ; 88ffff35
   0x55BE78: b        #0x55be9c ; 09000014
   0x55BE7C: mov      x0, x20 ; e00314aa
   0x55BE80: clrex     ; 5f3f03d5
   0x55BE84: bl       #0x3160670 ; fb11b094
   0x55BE88: ldaxrb   w8, [x21] ; a8fe5f08
   0x55BE8C: cmp      w8, #0x5f ; 1f7d0171
   0x55BE90: b.ne     #0x55be7c ; 61ffff54
   0x55BE94: stxrb    w8, w22, [x21] ; b67e0808
   0x55BE98: cbnz     w8, #0x55be88 ; 88ffff35
   0x55BE9C: ldxrb    w8, [x23] ; e87e5f08
   0x55BEA0: sub      w8, w8, #1 ; 08050051
   0x55BEA4: stxrb    w9, w8, [x23] ; e87e0908
   0x55BEA8: cbnz     w9, #0x55be9c ; a9ffff35
   0x55BEAC: mov      x0, x19 ; e00313aa
   0x55BEB0: bl       #0x3b50 ; 289fea97
   0x55BEB4: ldrh     w8, [x0] ; 08004079
   0x55BEB8: mov      w9, #0x5f ; e90b8052
   0x55BEBC: ldxrb    wzr, [x21] ; bf7e5f08
   0x55BEC0: stlxrb   w10, w9, [x21] ; a9fe0a08
   0x55BEC4: cbnz     w10, #0x55bebc ; caffff35
   0x55BEC8: dmb      ish ; bf3b03d5
   0x55BECC: lsr      w21, w8, #8 ; 157d0853
   0x55BED0: ldrb     w8, [x19, #0x123] ; 688e4439
   0x55BED4: cbnz     w8, #0x55bf54 ; 08040035
   0x55BED8: and      w8, w21, #7 ; a80a0012
   0x55BEDC: cmp      w8, #3 ; 1f0d0071
   0x55BEE0: b.ne     #0x55bf3c ; e1020054
   0x55BEE4: ldr      s0, [x19, #0x2c4] ; 60c642bd
   0x55BEE8: fmov     s1, #0.50000000 ; 01102c1e
   0x55BEEC: add      x8, x19, #0x2a0 ; 68820a91
   0x55BEF0: add      x9, x19, #0x2c0 ; 69020b91
   0x55BEF4: fmadd    s0, s0, s1, s8 ; 0020011f
~~~

## Static PC 0x656298 (word 0x9400033A)

- ELF file offset: 0x656CE0; opcode: BL; mask: to native_pid_shiny_mode_generator (0x656F80)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
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
>> 0x656298: bl       #0x656f80 ; 3a030094
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
~~~

## Static PC 0x657124 (word 0x94201831)

- ELF file offset: 0x657B6C; opcode: BL; mask: to shiny_xor_check (0xE5D1E8)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x656EA4: bl       #0x2cd754 ; 2cdaf197
   0x656EA8: mov      w8, #0x90 ; 08128052
   0x656EAC: movk     w8, #8, lsl #16 ; 0801a072
   0x656EB0: str      w8, [x20, #0x18] ; 881a00b9
   0x656EB4: stp      x22, x20, [x20, #8] ; 96d200a9
   0x656EB8: ldr      x8, [x23, #0x98] ; e84e40f9
   0x656EBC: sub      x8, x8, #1 ; 080500d1
   0x656EC0: str      x8, [x23, #0x98] ; e84e00f9
   0x656EC4: add      x8, x20, #0x28 ; 88a20091
   0x656EC8: ldaxr    w9, [x8] ; 09fd5f88
   0x656ECC: add      w10, w9, #1 ; 2a050011
   0x656ED0: stlxr    w11, w10, [x8] ; 0afd0b88
   0x656ED4: cbnz     w11, #0x656ec8 ; abffff35
   0x656ED8: cmn      w9, #1 ; 3f050031
   0x656EDC: b.eq     #0x656f44 ; 40030054
   0x656EE0: ldr      x0, [x19, #0x50] ; 602a40f9
   0x656EE4: str      xzr, [x19, #0x50] ; 7f2a00f9
   0x656EE8: cbz      x0, #0x656f08 ; 000100b4
   0x656EEC: add      x9, x0, #0x28 ; 09a00091
   0x656EF0: ldaxr    w8, [x9] ; 28fd5f88
   0x656EF4: subs     w10, w8, #1 ; 0a050071
   0x656EF8: stlxr    w11, w10, [x9] ; 2afd0b88
   0x656EFC: cbnz     w11, #0x656ef0 ; abffff35
   0x656F00: b.eq     #0x656f20 ; 00010054
   0x656F04: cbz      w8, #0x656f44 ; 08020034
   0x656F08: str      x20, [x19, #0x50] ; 742a00f9
   0x656F0C: ldp      x20, x19, [sp, #0x30] ; f44f43a9
   0x656F10: ldp      x22, x21, [sp, #0x20] ; f65742a9
   0x656F14: ldr      x23, [sp, #0x10] ; f70b40f9
   0x656F18: ldp      x29, x30, [sp], #0x40 ; fd7bc4a8
   0x656F1C: ret       ; c0035fd6
   0x656F20: ldr      x8, [x0] ; 080040f9
   0x656F24: ldr      x8, [x8, #0x10] ; 080940f9
   0x656F28: blr      x8 ; 00013fd6
   0x656F2C: b        #0x656f08 ; f7ffff17
   0x656F30: bl       #0x2fa70 ; d062e797
   0x656F34: ldr      x8, [x22] ; c80240f9
   0x656F38: mov      x0, x22 ; e00316aa
   0x656F3C: ldr      x8, [x8, #0xe8] ; 087540f9
   0x656F40: blr      x8 ; 00013fd6
   0x656F44: bl       #0x3160640 ; bf25ac94
   0x656F48: and      w8, w1, #0xff ; 281c0012
   0x656F4C: cmp      w8, #5 ; 1f150071
   0x656F50: b.hi     #0x656f5c ; 68000054
   0x656F54: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F58: strh     w2, [x8, #0x48] ; 02910079
   0x656F5C: ret       ; c0035fd6
   0x656F60: and      w8, w1, #0xff ; 281c0012
   0x656F64: cmp      w8, #5 ; 1f150071
   0x656F68: b.hi     #0x656f74 ; 68000054
   0x656F6C: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F70: strh     w2, [x8, #0x54] ; 02a90079
   0x656F74: ret       ; c0035fd6
   0x656F78: udf      #0 ; 00000000
   0x656F7C: udf      #0 ; 00000000
   0x656F80: sub      sp, sp, #0x50 ; ff4301d1
   0x656F84: stp      x29, x30, [sp, #0x20] ; fd7b02a9
   0x656F88: stp      x22, x21, [sp, #0x30] ; f65703a9
   0x656F8C: stp      x20, x19, [sp, #0x40] ; f44f04a9
   0x656F90: add      x29, sp, #0x20 ; fd830091
   0x656F94: mov      x8, #0x8960 ; 082c91d2
   0x656F98: movk     x8, #0x79f1, lsl #16 ; 283eaff2
   0x656F9C: str      xzr, [sp, #0x18] ; ff0f00f9
   0x656FA0: mov      x9, #0x6a5b ; 694b8dd2
   0x656FA4: movk     x9, #0x229d, lsl #16 ; a953a4f2
   0x656FA8: movk     x8, #0x17a5, lsl #32 ; a8f4c2f2
   0x656FAC: movk     x8, #0xf4b, lsl #48 ; 68e9e1f2
   0x656FB0: movk     x9, #0xb175, lsl #32 ; a92ed6f2
   0x656FB4: movk     x9, #0x82a2, lsl #48 ; 4954f0f2
   0x656FB8: stp      x8, x9, [sp, #8] ; e8a700a9
   0x656FBC: ldrb     w8, [x0, #8] ; 08204039
   0x656FC0: mov      x19, x0 ; f30300aa
   0x656FC4: cbz      w8, #0x656ff0 ; 68010034
   0x656FC8: ldr      x1, [x19] ; 610240f9
   0x656FCC: add      x0, sp, #8 ; e0230091
   0x656FD0: bl       #0xe5ec58 ; 221f2094
   0x656FD4: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FD8: cmn      x8, #1 ; 1f0500b1
   0x656FDC: b.eq     #0x657004 ; 40010054
   0x656FE0: ldr      x0, [x19, #0x18] ; 600e40f9
   0x656FE4: cmn      x0, #1 ; 1f0400b1
   0x656FE8: b.ne     #0x657078 ; 81040054
   0x656FEC: b        #0x657044 ; 16000014
   0x656FF0: add      x0, sp, #8 ; e0230091
   0x656FF4: bl       #0xe5ec14 ; 081f2094
   0x656FF8: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FFC: cmn      x8, #1 ; 1f0500b1
   0x657000: b.ne     #0x656fe0 ; 01ffff54
   0x657004: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657008: nop       ; 1f2003d5
   0x65700C: nop       ; 1f2003d5
   0x657010: ror      x11, x8, #0x28 ; 0ba1c893
   0x657014: eor      x12, x8, x9 ; 0c0109ca
   0x657018: add      w10, w8, w9 ; 0a01090b
   0x65701C: ror      x9, x12, #0x1b ; 896dcc93
   0x657020: cmn      w10, #1 ; 5f050031
   0x657024: eor      x8, x11, x12, lsl #16 ; 68410cca
   0x657028: eor      x8, x8, x12 ; 08010cca
   0x65702C: b.eq     #0x657010 ; 20ffff54
   0x657030: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657034: str      x10, [x19, #0x10] ; 6a0a00f9
   0x657038: ldr      x0, [x19, #0x18] ; 600e40f9
   0x65703C: cmn      x0, #1 ; 1f0400b1
   0x657040: b.ne     #0x657078 ; c1010054
   0x657044: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657048: nop       ; 1f2003d5
   0x65704C: nop       ; 1f2003d5
   0x657050: ror      x10, x8, #0x28 ; 0aa1c893
   0x657054: eor      x11, x8, x9 ; 0b0109ca
   0x657058: add      w0, w8, w9 ; 0001090b
   0x65705C: ror      x9, x11, #0x1b ; 696dcb93
   0x657060: cmn      w0, #1 ; 1f040031
   0x657064: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x657068: eor      x8, x8, x11 ; 08010bca
   0x65706C: b.eq     #0x657050 ; 20ffff54
   0x657070: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657074: str      x0, [x19, #0x18] ; 600e00f9
   0x657078: ldr      x9, [x19, #0x20] ; 691240f9
   0x65707C: mov      x8, #-0xfffb00000001 ; 68ffdf92
   0x657080: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657084: cmp      x9, x8 ; 3f0108eb
   0x657088: mov      x8, #-0xfffd00000001 ; a8ffdf92
   0x65708C: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657090: b.ne     #0x6570c4 ; a1010054
   0x657094: ldp      x9, x10, [sp, #8] ; e9ab40a9
   0x657098: eor      x12, x10, x9 ; 4c0109ca
   0x65709C: ror      x11, x9, #0x28 ; 2ba1c993
   0x6570A0: add      w9, w10, w9 ; 4901090b
   0x6570A4: ror      x13, x12, #0x1b ; 8d6dcc93
   0x6570A8: tst      x9, #1 ; 3f0140f2
   0x6570AC: eor      x10, x11, x12, lsl #16 ; 6a410cca
   0x6570B0: eor      x9, x10, x12 ; 49010cca
   0x6570B4: stp      x9, x13, [sp, #8] ; e9b700a9
   0x6570B8: mov      x9, #0x1ffffffff ; e98340b2
   0x6570BC: csel     x9, x9, x8, eq ; 2901889a
   0x6570C0: str      x9, [x19, #0x20] ; 691200f9
   0x6570C4: mov      x10, #0x1ffffffff ; ea8340b2
   0x6570C8: cmp      x9, x10 ; 3f010aeb
   0x6570CC: b.eq     #0x657140 ; a0030054
   0x6570D0: cmp      x9, x8 ; 3f0108eb
   0x6570D4: b.eq     #0x657170 ; e0040054
   0x6570D8: mov      x8, #0x3ffffffff ; e88740b2
   0x6570DC: cmp      x9, x8 ; 3f0108eb
   0x6570E0: b.ne     #0x6571a4 ; 21060054
   0x6570E4: ldrb     w8, [x19, #0x28] ; 68a24039
   0x6570E8: cbz      w8, #0x6571a4 ; e8050034
   0x6570EC: mov      w20, wzr ; f4031f2a
   0x6570F0: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6570F4: ror      x10, x8, #0x28 ; 0aa1c893
   0x6570F8: eor      x11, x8, x9 ; 0b0109ca
   0x6570FC: add      x1, x8, x9 ; 0101098b
   0x657100: ror      x9, x11, #0x1b ; 696dcb93
   0x657104: cmn      w1, #1 ; 3f040031
   0x657108: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65710C: eor      x8, x8, x11 ; 08010bca
   0x657110: b.eq     #0x6570f4 ; 20ffff54
   0x657114: ldr      w0, [x19, #0x18] ; 601a40b9
   0x657118: stp      x8, x9, [sp, #8] ; e8a700a9
   0x65711C: and      x8, x1, #0xffffffff ; 287c4092
   0x657120: str      x8, [x19, #0x20] ; 681200f9
>> 0x657124: bl       #0xe5d1e8 ; 31182094
   0x657128: tbnz     w0, #0, #0x6571a4 ; e0030037
   0x65712C: ldrb     w8, [x19, #0x28] ; 68a24039
   0x657130: add      w20, w20, #1 ; 94060011
   0x657134: cmp      w20, w8 ; 9f02086b
   0x657138: b.lo     #0x6570f0 ; c3fdff54
   0x65713C: b        #0x6571a4 ; 1a000014
   0x657140: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657144: ror      x10, x8, #0x28 ; 0aa1c893
   0x657148: eor      x11, x8, x9 ; 0b0109ca
   0x65714C: add      w1, w8, w9 ; 0101090b
   0x657150: ror      x9, x11, #0x1b ; 696dcb93
   0x657154: cmn      w1, #1 ; 3f040031
   0x657158: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65715C: eor      x8, x8, x11 ; 08010bca
   0x657160: b.eq     #0x657144 ; 20ffff54
   0x657164: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657168: bl       #0xe5d200 ; 26182094
   0x65716C: b        #0x65719c ; 0c000014
   0x657170: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657174: ror      x10, x8, #0x28 ; 0aa1c893
   0x657178: eor      x11, x8, x9 ; 0b0109ca
   0x65717C: add      w1, w8, w9 ; 0101090b
   0x657180: ror      x9, x11, #0x1b ; 696dcb93
   0x657184: cmn      w1, #1 ; 3f040031
   0x657188: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65718C: eor      x8, x8, x11 ; 08010bca
   0x657190: b.eq     #0x657174 ; 20ffff54
   0x657194: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657198: bl       #0xe5d21c ; 21182094
   0x65719C: mov      w8, w0 ; e803002a
   0x6571A0: str      x8, [x19, #0x20] ; 681200f9
   0x6571A4: ldrh     w8, [x19, #0x38] ; 68724079
   0x6571A8: cmp      w8, #0xff ; 1ffd0371
   0x6571AC: b.eq     #0x6571ec ; 00020054
   0x6571B0: cmp      w8, #0x65 ; 1f950171
   0x6571B4: b.hs     #0x657228 ; a2030054
   0x6571B8: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x6571BC: cbz      w10, #0x657238 ; ea030034
   0x6571C0: cmp      w10, #6 ; 5f190071
   0x6571C4: mov      x12, #-1 ; 0c008092
   0x6571C8: b.lo     #0x657748 ; 032c0054
   0x6571CC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571D0: strb     wzr, [x19, #0x66] ; 7f9a0139
   0x6571D4: str      x12, [x19, #0x48] ; 6c2600f9
   0x6571D8: str      w12, [x19, #0x50] ; 6c5200b9
   0x6571DC: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x6571E0: cmn      w10, #1 ; 5f050031
   0x6571E4: b.ne     #0x65726c ; 41040054
   0x6571E8: b        #0x657248 ; 18000014
   0x6571EC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571F0: add      w10, w8, w9 ; 0a01090b
   0x6571F4: eor      x11, x8, x9 ; 0b0109ca
   0x6571F8: and      x10, x10, #0x7f ; 4a194092
   0x6571FC: ror      x8, x8, #0x28 ; 08a1c893
   0x657200: eor      x8, x8, x11, lsl #16 ; 08410bca
   0x657204: ror      x9, x11, #0x1b ; 696dcb93
   0x657208: cmp      w10, #0x63 ; 5f8d0171
   0x65720C: eor      x8, x8, x11 ; 08010bca
   0x657210: b.hi     #0x6571f0 ; 08ffff54
   0x657214: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657218: add      w8, w10, #1 ; 48050011
   0x65721C: strh     w8, [x19, #0x38] ; 68720079
   0x657220: cmp      w8, #0x65 ; 1f950171
   0x657224: b.lo     #0x6571b8 ; a3fcff54
   0x657228: mov      w8, #0x64 ; 880c8052
   0x65722C: strh     w8, [x19, #0x38] ; 68720079
   0x657230: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x657234: cbnz     w10, #0x6571c0 ; 6afcff35
   0x657238: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x65723C: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x657240: cmn      w10, #1 ; 5f050031
   0x657244: b.ne     #0x65726c ; 41010054
~~~

## Static PC 0x657168 (word 0x94201826)

- ELF file offset: 0x657BB0; opcode: BL; mask: to pid_anti_shiny_if_needed_a (0xE5D200)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x656EE8: cbz      x0, #0x656f08 ; 000100b4
   0x656EEC: add      x9, x0, #0x28 ; 09a00091
   0x656EF0: ldaxr    w8, [x9] ; 28fd5f88
   0x656EF4: subs     w10, w8, #1 ; 0a050071
   0x656EF8: stlxr    w11, w10, [x9] ; 2afd0b88
   0x656EFC: cbnz     w11, #0x656ef0 ; abffff35
   0x656F00: b.eq     #0x656f20 ; 00010054
   0x656F04: cbz      w8, #0x656f44 ; 08020034
   0x656F08: str      x20, [x19, #0x50] ; 742a00f9
   0x656F0C: ldp      x20, x19, [sp, #0x30] ; f44f43a9
   0x656F10: ldp      x22, x21, [sp, #0x20] ; f65742a9
   0x656F14: ldr      x23, [sp, #0x10] ; f70b40f9
   0x656F18: ldp      x29, x30, [sp], #0x40 ; fd7bc4a8
   0x656F1C: ret       ; c0035fd6
   0x656F20: ldr      x8, [x0] ; 080040f9
   0x656F24: ldr      x8, [x8, #0x10] ; 080940f9
   0x656F28: blr      x8 ; 00013fd6
   0x656F2C: b        #0x656f08 ; f7ffff17
   0x656F30: bl       #0x2fa70 ; d062e797
   0x656F34: ldr      x8, [x22] ; c80240f9
   0x656F38: mov      x0, x22 ; e00316aa
   0x656F3C: ldr      x8, [x8, #0xe8] ; 087540f9
   0x656F40: blr      x8 ; 00013fd6
   0x656F44: bl       #0x3160640 ; bf25ac94
   0x656F48: and      w8, w1, #0xff ; 281c0012
   0x656F4C: cmp      w8, #5 ; 1f150071
   0x656F50: b.hi     #0x656f5c ; 68000054
   0x656F54: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F58: strh     w2, [x8, #0x48] ; 02910079
   0x656F5C: ret       ; c0035fd6
   0x656F60: and      w8, w1, #0xff ; 281c0012
   0x656F64: cmp      w8, #5 ; 1f150071
   0x656F68: b.hi     #0x656f74 ; 68000054
   0x656F6C: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F70: strh     w2, [x8, #0x54] ; 02a90079
   0x656F74: ret       ; c0035fd6
   0x656F78: udf      #0 ; 00000000
   0x656F7C: udf      #0 ; 00000000
   0x656F80: sub      sp, sp, #0x50 ; ff4301d1
   0x656F84: stp      x29, x30, [sp, #0x20] ; fd7b02a9
   0x656F88: stp      x22, x21, [sp, #0x30] ; f65703a9
   0x656F8C: stp      x20, x19, [sp, #0x40] ; f44f04a9
   0x656F90: add      x29, sp, #0x20 ; fd830091
   0x656F94: mov      x8, #0x8960 ; 082c91d2
   0x656F98: movk     x8, #0x79f1, lsl #16 ; 283eaff2
   0x656F9C: str      xzr, [sp, #0x18] ; ff0f00f9
   0x656FA0: mov      x9, #0x6a5b ; 694b8dd2
   0x656FA4: movk     x9, #0x229d, lsl #16 ; a953a4f2
   0x656FA8: movk     x8, #0x17a5, lsl #32 ; a8f4c2f2
   0x656FAC: movk     x8, #0xf4b, lsl #48 ; 68e9e1f2
   0x656FB0: movk     x9, #0xb175, lsl #32 ; a92ed6f2
   0x656FB4: movk     x9, #0x82a2, lsl #48 ; 4954f0f2
   0x656FB8: stp      x8, x9, [sp, #8] ; e8a700a9
   0x656FBC: ldrb     w8, [x0, #8] ; 08204039
   0x656FC0: mov      x19, x0 ; f30300aa
   0x656FC4: cbz      w8, #0x656ff0 ; 68010034
   0x656FC8: ldr      x1, [x19] ; 610240f9
   0x656FCC: add      x0, sp, #8 ; e0230091
   0x656FD0: bl       #0xe5ec58 ; 221f2094
   0x656FD4: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FD8: cmn      x8, #1 ; 1f0500b1
   0x656FDC: b.eq     #0x657004 ; 40010054
   0x656FE0: ldr      x0, [x19, #0x18] ; 600e40f9
   0x656FE4: cmn      x0, #1 ; 1f0400b1
   0x656FE8: b.ne     #0x657078 ; 81040054
   0x656FEC: b        #0x657044 ; 16000014
   0x656FF0: add      x0, sp, #8 ; e0230091
   0x656FF4: bl       #0xe5ec14 ; 081f2094
   0x656FF8: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FFC: cmn      x8, #1 ; 1f0500b1
   0x657000: b.ne     #0x656fe0 ; 01ffff54
   0x657004: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657008: nop       ; 1f2003d5
   0x65700C: nop       ; 1f2003d5
   0x657010: ror      x11, x8, #0x28 ; 0ba1c893
   0x657014: eor      x12, x8, x9 ; 0c0109ca
   0x657018: add      w10, w8, w9 ; 0a01090b
   0x65701C: ror      x9, x12, #0x1b ; 896dcc93
   0x657020: cmn      w10, #1 ; 5f050031
   0x657024: eor      x8, x11, x12, lsl #16 ; 68410cca
   0x657028: eor      x8, x8, x12 ; 08010cca
   0x65702C: b.eq     #0x657010 ; 20ffff54
   0x657030: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657034: str      x10, [x19, #0x10] ; 6a0a00f9
   0x657038: ldr      x0, [x19, #0x18] ; 600e40f9
   0x65703C: cmn      x0, #1 ; 1f0400b1
   0x657040: b.ne     #0x657078 ; c1010054
   0x657044: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657048: nop       ; 1f2003d5
   0x65704C: nop       ; 1f2003d5
   0x657050: ror      x10, x8, #0x28 ; 0aa1c893
   0x657054: eor      x11, x8, x9 ; 0b0109ca
   0x657058: add      w0, w8, w9 ; 0001090b
   0x65705C: ror      x9, x11, #0x1b ; 696dcb93
   0x657060: cmn      w0, #1 ; 1f040031
   0x657064: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x657068: eor      x8, x8, x11 ; 08010bca
   0x65706C: b.eq     #0x657050 ; 20ffff54
   0x657070: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657074: str      x0, [x19, #0x18] ; 600e00f9
   0x657078: ldr      x9, [x19, #0x20] ; 691240f9
   0x65707C: mov      x8, #-0xfffb00000001 ; 68ffdf92
   0x657080: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657084: cmp      x9, x8 ; 3f0108eb
   0x657088: mov      x8, #-0xfffd00000001 ; a8ffdf92
   0x65708C: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657090: b.ne     #0x6570c4 ; a1010054
   0x657094: ldp      x9, x10, [sp, #8] ; e9ab40a9
   0x657098: eor      x12, x10, x9 ; 4c0109ca
   0x65709C: ror      x11, x9, #0x28 ; 2ba1c993
   0x6570A0: add      w9, w10, w9 ; 4901090b
   0x6570A4: ror      x13, x12, #0x1b ; 8d6dcc93
   0x6570A8: tst      x9, #1 ; 3f0140f2
   0x6570AC: eor      x10, x11, x12, lsl #16 ; 6a410cca
   0x6570B0: eor      x9, x10, x12 ; 49010cca
   0x6570B4: stp      x9, x13, [sp, #8] ; e9b700a9
   0x6570B8: mov      x9, #0x1ffffffff ; e98340b2
   0x6570BC: csel     x9, x9, x8, eq ; 2901889a
   0x6570C0: str      x9, [x19, #0x20] ; 691200f9
   0x6570C4: mov      x10, #0x1ffffffff ; ea8340b2
   0x6570C8: cmp      x9, x10 ; 3f010aeb
   0x6570CC: b.eq     #0x657140 ; a0030054
   0x6570D0: cmp      x9, x8 ; 3f0108eb
   0x6570D4: b.eq     #0x657170 ; e0040054
   0x6570D8: mov      x8, #0x3ffffffff ; e88740b2
   0x6570DC: cmp      x9, x8 ; 3f0108eb
   0x6570E0: b.ne     #0x6571a4 ; 21060054
   0x6570E4: ldrb     w8, [x19, #0x28] ; 68a24039
   0x6570E8: cbz      w8, #0x6571a4 ; e8050034
   0x6570EC: mov      w20, wzr ; f4031f2a
   0x6570F0: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6570F4: ror      x10, x8, #0x28 ; 0aa1c893
   0x6570F8: eor      x11, x8, x9 ; 0b0109ca
   0x6570FC: add      x1, x8, x9 ; 0101098b
   0x657100: ror      x9, x11, #0x1b ; 696dcb93
   0x657104: cmn      w1, #1 ; 3f040031
   0x657108: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65710C: eor      x8, x8, x11 ; 08010bca
   0x657110: b.eq     #0x6570f4 ; 20ffff54
   0x657114: ldr      w0, [x19, #0x18] ; 601a40b9
   0x657118: stp      x8, x9, [sp, #8] ; e8a700a9
   0x65711C: and      x8, x1, #0xffffffff ; 287c4092
   0x657120: str      x8, [x19, #0x20] ; 681200f9
   0x657124: bl       #0xe5d1e8 ; 31182094
   0x657128: tbnz     w0, #0, #0x6571a4 ; e0030037
   0x65712C: ldrb     w8, [x19, #0x28] ; 68a24039
   0x657130: add      w20, w20, #1 ; 94060011
   0x657134: cmp      w20, w8 ; 9f02086b
   0x657138: b.lo     #0x6570f0 ; c3fdff54
   0x65713C: b        #0x6571a4 ; 1a000014
   0x657140: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657144: ror      x10, x8, #0x28 ; 0aa1c893
   0x657148: eor      x11, x8, x9 ; 0b0109ca
   0x65714C: add      w1, w8, w9 ; 0101090b
   0x657150: ror      x9, x11, #0x1b ; 696dcb93
   0x657154: cmn      w1, #1 ; 3f040031
   0x657158: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65715C: eor      x8, x8, x11 ; 08010bca
   0x657160: b.eq     #0x657144 ; 20ffff54
   0x657164: stp      x8, x9, [sp, #8] ; e8a700a9
>> 0x657168: bl       #0xe5d200 ; 26182094
   0x65716C: b        #0x65719c ; 0c000014
   0x657170: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657174: ror      x10, x8, #0x28 ; 0aa1c893
   0x657178: eor      x11, x8, x9 ; 0b0109ca
   0x65717C: add      w1, w8, w9 ; 0101090b
   0x657180: ror      x9, x11, #0x1b ; 696dcb93
   0x657184: cmn      w1, #1 ; 3f040031
   0x657188: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65718C: eor      x8, x8, x11 ; 08010bca
   0x657190: b.eq     #0x657174 ; 20ffff54
   0x657194: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657198: bl       #0xe5d21c ; 21182094
   0x65719C: mov      w8, w0 ; e803002a
   0x6571A0: str      x8, [x19, #0x20] ; 681200f9
   0x6571A4: ldrh     w8, [x19, #0x38] ; 68724079
   0x6571A8: cmp      w8, #0xff ; 1ffd0371
   0x6571AC: b.eq     #0x6571ec ; 00020054
   0x6571B0: cmp      w8, #0x65 ; 1f950171
   0x6571B4: b.hs     #0x657228 ; a2030054
   0x6571B8: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x6571BC: cbz      w10, #0x657238 ; ea030034
   0x6571C0: cmp      w10, #6 ; 5f190071
   0x6571C4: mov      x12, #-1 ; 0c008092
   0x6571C8: b.lo     #0x657748 ; 032c0054
   0x6571CC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571D0: strb     wzr, [x19, #0x66] ; 7f9a0139
   0x6571D4: str      x12, [x19, #0x48] ; 6c2600f9
   0x6571D8: str      w12, [x19, #0x50] ; 6c5200b9
   0x6571DC: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x6571E0: cmn      w10, #1 ; 5f050031
   0x6571E4: b.ne     #0x65726c ; 41040054
   0x6571E8: b        #0x657248 ; 18000014
   0x6571EC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571F0: add      w10, w8, w9 ; 0a01090b
   0x6571F4: eor      x11, x8, x9 ; 0b0109ca
   0x6571F8: and      x10, x10, #0x7f ; 4a194092
   0x6571FC: ror      x8, x8, #0x28 ; 08a1c893
   0x657200: eor      x8, x8, x11, lsl #16 ; 08410bca
   0x657204: ror      x9, x11, #0x1b ; 696dcb93
   0x657208: cmp      w10, #0x63 ; 5f8d0171
   0x65720C: eor      x8, x8, x11 ; 08010bca
   0x657210: b.hi     #0x6571f0 ; 08ffff54
   0x657214: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657218: add      w8, w10, #1 ; 48050011
   0x65721C: strh     w8, [x19, #0x38] ; 68720079
   0x657220: cmp      w8, #0x65 ; 1f950171
   0x657224: b.lo     #0x6571b8 ; a3fcff54
   0x657228: mov      w8, #0x64 ; 880c8052
   0x65722C: strh     w8, [x19, #0x38] ; 68720079
   0x657230: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x657234: cbnz     w10, #0x6571c0 ; 6afcff35
   0x657238: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x65723C: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x657240: cmn      w10, #1 ; 5f050031
   0x657244: b.ne     #0x65726c ; 41010054
   0x657248: ror      x10, x8, #0x28 ; 0aa1c893
   0x65724C: eor      x11, x9, x8 ; 2b0108ca
   0x657250: add      w12, w9, w8 ; 2c01080b
   0x657254: ror      x9, x11, #0x1b ; 696dcb93
   0x657258: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65725C: and      w10, w12, #0x1f ; 8a110012
   0x657260: strh     w10, [x19, #0x48] ; 6a920079
   0x657264: eor      x8, x8, x11 ; 08010bca
   0x657268: stp      x8, x9, [sp, #8] ; e8a700a9
   0x65726C: ldrsh    w10, [x19, #0x4a] ; 6a96c079
   0x657270: cmn      w10, #1 ; 5f050031
   0x657274: b.eq     #0x65732c ; c0050054
   0x657278: ldrsh    w10, [x19, #0x4c] ; 6a9ac079
   0x65727C: cmn      w10, #1 ; 5f050031
   0x657280: b.eq     #0x65735c ; e0060054
   0x657284: ldrsh    w10, [x19, #0x4e] ; 6a9ec079
   0x657288: cmn      w10, #1 ; 5f050031
~~~

## Static PC 0x657198 (word 0x94201821)

- ELF file offset: 0x657BE0; opcode: BL; mask: to pid_shiny_adjust_candidate (0xE5D21C)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x656F18: ldp      x29, x30, [sp], #0x40 ; fd7bc4a8
   0x656F1C: ret       ; c0035fd6
   0x656F20: ldr      x8, [x0] ; 080040f9
   0x656F24: ldr      x8, [x8, #0x10] ; 080940f9
   0x656F28: blr      x8 ; 00013fd6
   0x656F2C: b        #0x656f08 ; f7ffff17
   0x656F30: bl       #0x2fa70 ; d062e797
   0x656F34: ldr      x8, [x22] ; c80240f9
   0x656F38: mov      x0, x22 ; e00316aa
   0x656F3C: ldr      x8, [x8, #0xe8] ; 087540f9
   0x656F40: blr      x8 ; 00013fd6
   0x656F44: bl       #0x3160640 ; bf25ac94
   0x656F48: and      w8, w1, #0xff ; 281c0012
   0x656F4C: cmp      w8, #5 ; 1f150071
   0x656F50: b.hi     #0x656f5c ; 68000054
   0x656F54: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F58: strh     w2, [x8, #0x48] ; 02910079
   0x656F5C: ret       ; c0035fd6
   0x656F60: and      w8, w1, #0xff ; 281c0012
   0x656F64: cmp      w8, #5 ; 1f150071
   0x656F68: b.hi     #0x656f74 ; 68000054
   0x656F6C: add      x8, x0, w1, uxtb #1 ; 0804218b
   0x656F70: strh     w2, [x8, #0x54] ; 02a90079
   0x656F74: ret       ; c0035fd6
   0x656F78: udf      #0 ; 00000000
   0x656F7C: udf      #0 ; 00000000
   0x656F80: sub      sp, sp, #0x50 ; ff4301d1
   0x656F84: stp      x29, x30, [sp, #0x20] ; fd7b02a9
   0x656F88: stp      x22, x21, [sp, #0x30] ; f65703a9
   0x656F8C: stp      x20, x19, [sp, #0x40] ; f44f04a9
   0x656F90: add      x29, sp, #0x20 ; fd830091
   0x656F94: mov      x8, #0x8960 ; 082c91d2
   0x656F98: movk     x8, #0x79f1, lsl #16 ; 283eaff2
   0x656F9C: str      xzr, [sp, #0x18] ; ff0f00f9
   0x656FA0: mov      x9, #0x6a5b ; 694b8dd2
   0x656FA4: movk     x9, #0x229d, lsl #16 ; a953a4f2
   0x656FA8: movk     x8, #0x17a5, lsl #32 ; a8f4c2f2
   0x656FAC: movk     x8, #0xf4b, lsl #48 ; 68e9e1f2
   0x656FB0: movk     x9, #0xb175, lsl #32 ; a92ed6f2
   0x656FB4: movk     x9, #0x82a2, lsl #48 ; 4954f0f2
   0x656FB8: stp      x8, x9, [sp, #8] ; e8a700a9
   0x656FBC: ldrb     w8, [x0, #8] ; 08204039
   0x656FC0: mov      x19, x0 ; f30300aa
   0x656FC4: cbz      w8, #0x656ff0 ; 68010034
   0x656FC8: ldr      x1, [x19] ; 610240f9
   0x656FCC: add      x0, sp, #8 ; e0230091
   0x656FD0: bl       #0xe5ec58 ; 221f2094
   0x656FD4: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FD8: cmn      x8, #1 ; 1f0500b1
   0x656FDC: b.eq     #0x657004 ; 40010054
   0x656FE0: ldr      x0, [x19, #0x18] ; 600e40f9
   0x656FE4: cmn      x0, #1 ; 1f0400b1
   0x656FE8: b.ne     #0x657078 ; 81040054
   0x656FEC: b        #0x657044 ; 16000014
   0x656FF0: add      x0, sp, #8 ; e0230091
   0x656FF4: bl       #0xe5ec14 ; 081f2094
   0x656FF8: ldr      x8, [x19, #0x10] ; 680a40f9
   0x656FFC: cmn      x8, #1 ; 1f0500b1
   0x657000: b.ne     #0x656fe0 ; 01ffff54
   0x657004: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657008: nop       ; 1f2003d5
   0x65700C: nop       ; 1f2003d5
   0x657010: ror      x11, x8, #0x28 ; 0ba1c893
   0x657014: eor      x12, x8, x9 ; 0c0109ca
   0x657018: add      w10, w8, w9 ; 0a01090b
   0x65701C: ror      x9, x12, #0x1b ; 896dcc93
   0x657020: cmn      w10, #1 ; 5f050031
   0x657024: eor      x8, x11, x12, lsl #16 ; 68410cca
   0x657028: eor      x8, x8, x12 ; 08010cca
   0x65702C: b.eq     #0x657010 ; 20ffff54
   0x657030: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657034: str      x10, [x19, #0x10] ; 6a0a00f9
   0x657038: ldr      x0, [x19, #0x18] ; 600e40f9
   0x65703C: cmn      x0, #1 ; 1f0400b1
   0x657040: b.ne     #0x657078 ; c1010054
   0x657044: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657048: nop       ; 1f2003d5
   0x65704C: nop       ; 1f2003d5
   0x657050: ror      x10, x8, #0x28 ; 0aa1c893
   0x657054: eor      x11, x8, x9 ; 0b0109ca
   0x657058: add      w0, w8, w9 ; 0001090b
   0x65705C: ror      x9, x11, #0x1b ; 696dcb93
   0x657060: cmn      w0, #1 ; 1f040031
   0x657064: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x657068: eor      x8, x8, x11 ; 08010bca
   0x65706C: b.eq     #0x657050 ; 20ffff54
   0x657070: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657074: str      x0, [x19, #0x18] ; 600e00f9
   0x657078: ldr      x9, [x19, #0x20] ; 691240f9
   0x65707C: mov      x8, #-0xfffb00000001 ; 68ffdf92
   0x657080: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657084: cmp      x9, x8 ; 3f0108eb
   0x657088: mov      x8, #-0xfffd00000001 ; a8ffdf92
   0x65708C: movk     x8, #0, lsl #48 ; 0800e0f2
   0x657090: b.ne     #0x6570c4 ; a1010054
   0x657094: ldp      x9, x10, [sp, #8] ; e9ab40a9
   0x657098: eor      x12, x10, x9 ; 4c0109ca
   0x65709C: ror      x11, x9, #0x28 ; 2ba1c993
   0x6570A0: add      w9, w10, w9 ; 4901090b
   0x6570A4: ror      x13, x12, #0x1b ; 8d6dcc93
   0x6570A8: tst      x9, #1 ; 3f0140f2
   0x6570AC: eor      x10, x11, x12, lsl #16 ; 6a410cca
   0x6570B0: eor      x9, x10, x12 ; 49010cca
   0x6570B4: stp      x9, x13, [sp, #8] ; e9b700a9
   0x6570B8: mov      x9, #0x1ffffffff ; e98340b2
   0x6570BC: csel     x9, x9, x8, eq ; 2901889a
   0x6570C0: str      x9, [x19, #0x20] ; 691200f9
   0x6570C4: mov      x10, #0x1ffffffff ; ea8340b2
   0x6570C8: cmp      x9, x10 ; 3f010aeb
   0x6570CC: b.eq     #0x657140 ; a0030054
   0x6570D0: cmp      x9, x8 ; 3f0108eb
   0x6570D4: b.eq     #0x657170 ; e0040054
   0x6570D8: mov      x8, #0x3ffffffff ; e88740b2
   0x6570DC: cmp      x9, x8 ; 3f0108eb
   0x6570E0: b.ne     #0x6571a4 ; 21060054
   0x6570E4: ldrb     w8, [x19, #0x28] ; 68a24039
   0x6570E8: cbz      w8, #0x6571a4 ; e8050034
   0x6570EC: mov      w20, wzr ; f4031f2a
   0x6570F0: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6570F4: ror      x10, x8, #0x28 ; 0aa1c893
   0x6570F8: eor      x11, x8, x9 ; 0b0109ca
   0x6570FC: add      x1, x8, x9 ; 0101098b
   0x657100: ror      x9, x11, #0x1b ; 696dcb93
   0x657104: cmn      w1, #1 ; 3f040031
   0x657108: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65710C: eor      x8, x8, x11 ; 08010bca
   0x657110: b.eq     #0x6570f4 ; 20ffff54
   0x657114: ldr      w0, [x19, #0x18] ; 601a40b9
   0x657118: stp      x8, x9, [sp, #8] ; e8a700a9
   0x65711C: and      x8, x1, #0xffffffff ; 287c4092
   0x657120: str      x8, [x19, #0x20] ; 681200f9
   0x657124: bl       #0xe5d1e8 ; 31182094
   0x657128: tbnz     w0, #0, #0x6571a4 ; e0030037
   0x65712C: ldrb     w8, [x19, #0x28] ; 68a24039
   0x657130: add      w20, w20, #1 ; 94060011
   0x657134: cmp      w20, w8 ; 9f02086b
   0x657138: b.lo     #0x6570f0 ; c3fdff54
   0x65713C: b        #0x6571a4 ; 1a000014
   0x657140: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657144: ror      x10, x8, #0x28 ; 0aa1c893
   0x657148: eor      x11, x8, x9 ; 0b0109ca
   0x65714C: add      w1, w8, w9 ; 0101090b
   0x657150: ror      x9, x11, #0x1b ; 696dcb93
   0x657154: cmn      w1, #1 ; 3f040031
   0x657158: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65715C: eor      x8, x8, x11 ; 08010bca
   0x657160: b.eq     #0x657144 ; 20ffff54
   0x657164: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657168: bl       #0xe5d200 ; 26182094
   0x65716C: b        #0x65719c ; 0c000014
   0x657170: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x657174: ror      x10, x8, #0x28 ; 0aa1c893
   0x657178: eor      x11, x8, x9 ; 0b0109ca
   0x65717C: add      w1, w8, w9 ; 0101090b
   0x657180: ror      x9, x11, #0x1b ; 696dcb93
   0x657184: cmn      w1, #1 ; 3f040031
   0x657188: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65718C: eor      x8, x8, x11 ; 08010bca
   0x657190: b.eq     #0x657174 ; 20ffff54
   0x657194: stp      x8, x9, [sp, #8] ; e8a700a9
>> 0x657198: bl       #0xe5d21c ; 21182094
   0x65719C: mov      w8, w0 ; e803002a
   0x6571A0: str      x8, [x19, #0x20] ; 681200f9
   0x6571A4: ldrh     w8, [x19, #0x38] ; 68724079
   0x6571A8: cmp      w8, #0xff ; 1ffd0371
   0x6571AC: b.eq     #0x6571ec ; 00020054
   0x6571B0: cmp      w8, #0x65 ; 1f950171
   0x6571B4: b.hs     #0x657228 ; a2030054
   0x6571B8: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x6571BC: cbz      w10, #0x657238 ; ea030034
   0x6571C0: cmp      w10, #6 ; 5f190071
   0x6571C4: mov      x12, #-1 ; 0c008092
   0x6571C8: b.lo     #0x657748 ; 032c0054
   0x6571CC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571D0: strb     wzr, [x19, #0x66] ; 7f9a0139
   0x6571D4: str      x12, [x19, #0x48] ; 6c2600f9
   0x6571D8: str      w12, [x19, #0x50] ; 6c5200b9
   0x6571DC: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x6571E0: cmn      w10, #1 ; 5f050031
   0x6571E4: b.ne     #0x65726c ; 41040054
   0x6571E8: b        #0x657248 ; 18000014
   0x6571EC: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x6571F0: add      w10, w8, w9 ; 0a01090b
   0x6571F4: eor      x11, x8, x9 ; 0b0109ca
   0x6571F8: and      x10, x10, #0x7f ; 4a194092
   0x6571FC: ror      x8, x8, #0x28 ; 08a1c893
   0x657200: eor      x8, x8, x11, lsl #16 ; 08410bca
   0x657204: ror      x9, x11, #0x1b ; 696dcb93
   0x657208: cmp      w10, #0x63 ; 5f8d0171
   0x65720C: eor      x8, x8, x11 ; 08010bca
   0x657210: b.hi     #0x6571f0 ; 08ffff54
   0x657214: stp      x8, x9, [sp, #8] ; e8a700a9
   0x657218: add      w8, w10, #1 ; 48050011
   0x65721C: strh     w8, [x19, #0x38] ; 68720079
   0x657220: cmp      w8, #0x65 ; 1f950171
   0x657224: b.lo     #0x6571b8 ; a3fcff54
   0x657228: mov      w8, #0x64 ; 880c8052
   0x65722C: strh     w8, [x19, #0x38] ; 68720079
   0x657230: ldrb     w10, [x19, #0x66] ; 6a9a4139
   0x657234: cbnz     w10, #0x6571c0 ; 6afcff35
   0x657238: ldp      x8, x9, [sp, #8] ; e8a740a9
   0x65723C: ldrsh    w10, [x19, #0x48] ; 6a92c079
   0x657240: cmn      w10, #1 ; 5f050031
   0x657244: b.ne     #0x65726c ; 41010054
   0x657248: ror      x10, x8, #0x28 ; 0aa1c893
   0x65724C: eor      x11, x9, x8 ; 2b0108ca
   0x657250: add      w12, w9, w8 ; 2c01080b
   0x657254: ror      x9, x11, #0x1b ; 696dcb93
   0x657258: eor      x8, x10, x11, lsl #16 ; 48410bca
   0x65725C: and      w10, w12, #0x1f ; 8a110012
   0x657260: strh     w10, [x19, #0x48] ; 6a920079
   0x657264: eor      x8, x8, x11 ; 08010bca
   0x657268: stp      x8, x9, [sp, #8] ; e8a700a9
   0x65726C: ldrsh    w10, [x19, #0x4a] ; 6a96c079
   0x657270: cmn      w10, #1 ; 5f050031
   0x657274: b.eq     #0x65732c ; c0050054
   0x657278: ldrsh    w10, [x19, #0x4c] ; 6a9ac079
   0x65727C: cmn      w10, #1 ; 5f050031
   0x657280: b.eq     #0x65735c ; e0060054
   0x657284: ldrsh    w10, [x19, #0x4e] ; 6a9ec079
   0x657288: cmn      w10, #1 ; 5f050031
   0x65728C: b.eq     #0x65738c ; 00080054
   0x657290: ldrsh    w10, [x19, #0x50] ; 6aa2c079
   0x657294: cmn      w10, #1 ; 5f050031
   0x657298: b.eq     #0x6573bc ; 20090054
   0x65729C: ldrsh    w10, [x19, #0x52] ; 6aa6c079
   0x6572A0: cmn      w10, #1 ; 5f050031
   0x6572A4: b.eq     #0x6573ec ; 400a0054
   0x6572A8: ldrsh    w10, [x19, #0x54] ; 6aaac079
   0x6572AC: cmn      w10, #1 ; 5f050031
   0x6572B0: b.eq     #0x657420 ; 800b0054
   0x6572B4: ldrsh    w10, [x19, #0x56] ; 6aaec079
   0x6572B8: cmn      w10, #1 ; 5f050031
~~~

## Static PC 0xE3EB64 (word 0x97E06107)

- ELF file offset: 0xE3F5AC; opcode: BL; mask: to native_pid_shiny_mode_generator (0x656F80)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE3E8E4: stp      xzr, xzr, [x19, #0x78] ; 7ffe07a9
   0xE3E8E8: bl       #0x3f0784 ; a7c7d697
   0xE3E8EC: ldrb     w8, [x0, #0x378] ; 08e04d39
   0xE3E8F0: stur     wzr, [x23, #0x91] ; ff1209b8
   0xE3E8F4: stur     xzr, [x23, #0x81] ; ff1208f8
   0xE3E8F8: mov      w9, #4 ; 89008052
   0xE3E8FC: mov      w1, #0x148 ; 01298052
   0xE3E900: mov      w2, #4 ; 82008052
   0xE3E904: stur     xzr, [x23, #0x89] ; ff9208f8
   0xE3E908: stur     xzr, [x23, #0xda] ; ffa20df8
   0xE3E90C: stur     xzr, [x23, #0xe2] ; ff220ef8
   0xE3E910: stur     xzr, [x23, #0xea] ; ffa20ef8
   0xE3E914: stur     xzr, [x23, #0x96] ; ff6209f8
   0xE3E918: ldr      x23, [x19, #8] ; 770640f9
   0xE3E91C: mov      x0, x23 ; e00317aa
   0xE3E920: strb     w27, [sp, #0x9d] ; fb770239
   0xE3E924: strb     wzr, [sp, #0x88] ; ff230239
   0xE3E928: strb     wzr, [sp, #0xa6] ; ff9b0239
   0xE3E92C: strb     w9, [sp, #0x75] ; e9d70139
   0xE3E930: strb     w8, [sp, #0x74] ; e8d30139
   0xE3E934: str      xzr, [sp, #0x38] ; ff1f00f9
   0xE3E938: str      xzr, [sp, #0xd8] ; ff6f00f9
   0xE3E93C: strh     wzr, [sp, #0xe0] ; ffc30179
   0xE3E940: str      x26, [sp, #0x50] ; fa2b00f9
   0xE3E944: str      w26, [sp, #0x58] ; fa5b00b9
   0xE3E948: strh     wzr, [sp, #0xfa] ; fff70179
   0xE3E94C: stur     xzr, [sp, #0x5c] ; ffc305f8
   0xE3E950: stur     xzr, [sp, #0x64] ; ff4306f8
   0xE3E954: strh     wzr, [sp, #0x6c] ; ffdb0079
   0xE3E958: strh     w22, [sp, #0x32] ; f6670079
   0xE3E95C: strh     w21, [sp, #0x40] ; f5830079
   0xE3E960: str      x20, [sp, #0x20] ; f41300f9
   0xE3E964: stp      xzr, xzr, [sp, #0xa8] ; ffff0aa9
   0xE3E968: stp      xzr, xzr, [sp, #0xb8] ; ffff0ba9
   0xE3E96C: stp      xzr, xzr, [sp, #0xc8] ; ffff0ca9
   0xE3E970: stp      xzr, xzr, [sp, #0x78] ; ffff07a9
   0xE3E974: ldr      x8, [x23] ; e80240f9
   0xE3E978: ldr      x8, [x8, #0x10] ; 080940f9
   0xE3E97C: blr      x8 ; 00013fd6
   0xE3E980: mov      x20, x0 ; f40300aa
   0xE3E984: cbz      x0, #0xe3e9dc ; c00200b4
   0xE3E988: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E98C: cmp      x8, #0x10 ; 1f4100f1
   0xE3E990: b.eq     #0xe3eb30 ; 000d0054
   0xE3E994: add      x8, x24, x8, lsl #3 ; 080f088b
   0xE3E998: mov      w21, #0x148 ; 15298052
   0xE3E99C: mov      x0, x20 ; e00314aa
   0xE3E9A0: mov      w1, wzr ; e1031f2a
   0xE3E9A4: mov      x2, x21 ; e20315aa
   0xE3E9A8: str      x23, [x8, #0x18] ; 170d00f9
   0xE3E9AC: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E9B0: add      x8, x8, #1 ; 08050091
   0xE3E9B4: str      x8, [x24, #0x98] ; 084f00f9
   0xE3E9B8: bl       #0x3161520 ; da8a8c94
   0xE3E9BC: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E9C0: mov      w22, #4 ; 96008052
   0xE3E9C4: sub      x8, x8, #1 ; 080500d1
   0xE3E9C8: str      x8, [x24, #0x98] ; 084f00f9
   0xE3E9CC: ldr      x1, [x25] ; 210340f9
   0xE3E9D0: str      x20, [x25] ; 340300f9
   0xE3E9D4: cbnz     x1, #0xe3e9f4 ; 010100b5
   0xE3E9D8: b        #0xe3ea10 ; 0e000014
   0xE3E9DC: mov      x23, xzr ; f7031faa
   0xE3E9E0: mov      x21, xzr ; f5031faa
   0xE3E9E4: mov      x22, xzr ; f6031faa
   0xE3E9E8: ldr      x1, [x25] ; 210340f9
   0xE3E9EC: str      x20, [x25] ; 340300f9
   0xE3E9F0: cbz      x1, #0xe3ea10 ; 010100b4
   0xE3E9F4: ldr      x0, [x19, #0x38] ; 601e40f9
   0xE3E9F8: cbz      x0, #0xe3ea10 ; c00000b4
   0xE3E9FC: ldr      x8, [x0] ; 080040f9
   0xE3EA00: ldp      x2, x3, [x19, #0x40] ; 620e44a9
   0xE3EA04: ldr      x8, [x8, #0x18] ; 080d40f9
   0xE3EA08: blr      x8 ; 00013fd6
   0xE3EA0C: ldr      x20, [x19, #0x30] ; 741a40f9
   0xE3EA10: mov      w2, #0x148 ; 02298052
   0xE3EA14: mov      x0, x20 ; e00314aa
   0xE3EA18: str      x22, [x19, #0x48] ; 762600f9
   0xE3EA1C: mov      w1, wzr ; e1031f2a
   0xE3EA20: stp      x23, x21, [x19, #0x38] ; 77d603a9
   0xE3EA24: bl       #0x3161520 ; bf8a8c94
   0xE3EA28: ldr      x20, [x19, #8] ; 740640f9
   0xE3EA2C: mov      w1, #0x28 ; 01058052
   0xE3EA30: mov      w2, #8 ; 02018052
   0xE3EA34: ldr      x8, [x20] ; 880240f9
   0xE3EA38: mov      x0, x20 ; e00314aa
   0xE3EA3C: ldr      x8, [x8, #0x10] ; 080940f9
   0xE3EA40: blr      x8 ; 00013fd6
   0xE3EA44: mov      x21, x0 ; f50300aa
   0xE3EA48: cbz      x0, #0xe3ea98 ; 800200b4
   0xE3EA4C: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA50: cmp      x8, #0x10 ; 1f4100f1
   0xE3EA54: b.eq     #0xe3eb30 ; e0060054
   0xE3EA58: add      x8, x24, x8, lsl #3 ; 080f088b
   0xE3EA5C: mov      x0, x21 ; e00315aa
   0xE3EA60: str      x20, [x8, #0x18] ; 140d00f9
   0xE3EA64: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA68: add      x8, x8, #1 ; 08050091
   0xE3EA6C: str      x8, [x24, #0x98] ; 084f00f9
   0xE3EA70: bl       #0xe47564 ; bd220094
   0xE3EA74: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA78: mov      w23, #8 ; 17018052
   0xE3EA7C: sub      x8, x8, #1 ; 080500d1
   0xE3EA80: str      x8, [x24, #0x98] ; 084f00f9
   0xE3EA84: mov      w24, #0x28 ; 18058052
   0xE3EA88: ldr      x22, [x19, #0x70] ; 763a40f9
   0xE3EA8C: str      x21, [x19, #0x70] ; 753a00f9
   0xE3EA90: cbnz     x22, #0xe3eab0 ; 160100b5
   0xE3EA94: b        #0xe3eae4 ; 14000014
   0xE3EA98: mov      x20, xzr ; f4031faa
   0xE3EA9C: mov      x24, xzr ; f8031faa
   0xE3EAA0: mov      x23, xzr ; f7031faa
   0xE3EAA4: ldr      x22, [x19, #0x70] ; 763a40f9
   0xE3EAA8: str      x21, [x19, #0x70] ; 753a00f9
   0xE3EAAC: cbz      x22, #0xe3eae4 ; d60100b4
   0xE3EAB0: ldr      x8, [x19, #0x78] ; 683e40f9
   0xE3EAB4: cbz      x8, #0xe3eae4 ; 880100b4
   0xE3EAB8: ldr      x8, [x22] ; c80240f9
   0xE3EABC: mov      x0, x22 ; e00316aa
   0xE3EAC0: ldr      x8, [x8] ; 080140f9
   0xE3EAC4: blr      x8 ; 00013fd6
   0xE3EAC8: ldp      x0, x2, [x19, #0x78] ; 608a47a9
   0xE3EACC: mov      x1, x22 ; e10316aa
   0xE3EAD0: ldr      x3, [x19, #0x88] ; 634640f9
   0xE3EAD4: ldr      x8, [x0] ; 080040f9
   0xE3EAD8: ldr      x8, [x8, #0x18] ; 080d40f9
   0xE3EADC: blr      x8 ; 00013fd6
   0xE3EAE0: ldr      x21, [x19, #0x70] ; 753a40f9
   0xE3EAE4: ldr      x1, [x19, #0x30] ; 611a40f9
   0xE3EAE8: mov      x0, x21 ; e00315aa
   0xE3EAEC: mov      x2, xzr ; e2031faa
   0xE3EAF0: stp      x20, x24, [x19, #0x78] ; 74e207a9
   0xE3EAF4: str      x23, [x19, #0x88] ; 774600f9
   0xE3EAF8: bl       #0xe475fc ; c1220094
   0xE3EAFC: add      x1, sp, #8 ; e1230091
   0xE3EB00: mov      x0, x19 ; e00313aa
   0xE3EB04: bl       #0xe3eb34 ; 0c000094
   0xE3EB08: mov      x0, x19 ; e00313aa
   0xE3EB0C: bl       #0xe3f18c ; a0010094
   0xE3EB10: ldp      x20, x19, [sp, #0x150] ; f44f55a9
   0xE3EB14: ldp      x22, x21, [sp, #0x140] ; f65754a9
   0xE3EB18: ldp      x24, x23, [sp, #0x130] ; f85f53a9
   0xE3EB1C: ldp      x26, x25, [sp, #0x120] ; fa6752a9
   0xE3EB20: ldp      x28, x27, [sp, #0x110] ; fc6f51a9
   0xE3EB24: ldp      x29, x30, [sp, #0x100] ; fd7b50a9
   0xE3EB28: add      sp, sp, #0x160 ; ff830591
   0xE3EB2C: ret       ; c0035fd6
   0xE3EB30: bl       #0x2fa70 ; d0c3c797
   0xE3EB34: ldrh     w8, [x1, #0x2a] ; 28544079
   0xE3EB38: cbz      w8, #0xe3f188 ; 88320034
   0xE3EB3C: sub      sp, sp, #0x140 ; ff0305d1
   0xE3EB40: stp      x29, x30, [sp, #0x100] ; fd7b10a9
   0xE3EB44: str      x28, [sp, #0x110] ; fc8b00f9
   0xE3EB48: stp      x22, x21, [sp, #0x120] ; f65712a9
   0xE3EB4C: stp      x20, x19, [sp, #0x130] ; f44f13a9
   0xE3EB50: add      x29, sp, #0x100 ; fd030491
   0xE3EB54: mov      x19, x0 ; f30300aa
   0xE3EB58: add      x0, sp, #8 ; e0230091
   0xE3EB5C: bl       #0xbef804 ; 2ac3f697
   0xE3EB60: add      x0, sp, #8 ; e0230091
>> 0xE3EB64: bl       #0x656f80 ; 0761e097
   0xE3EB68: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB6C: bl       #0xe47a14 ; aa230094
   0xE3EB70: mov      w20, w0 ; f403002a
   0xE3EB74: tbnz     w0, #0, #0xe3eb80 ; 60000037
   0xE3EB78: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB7C: bl       #0xe480e0 ; 59250094
   0xE3EB80: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB84: bl       #0xe483c0 ; 0f260094
   0xE3EB88: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB8C: ldr      w1, [sp, #0x18] ; e11b40b9
   0xE3EB90: bl       #0xe514d0 ; 504a0094
   0xE3EB94: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB98: ldr      w1, [sp, #0x20] ; e12340b9
   0xE3EB9C: bl       #0xe52ee0 ; d1500094
   0xE3EBA0: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBA4: ldr      w1, [sp, #0x28] ; e12b40b9
   0xE3EBA8: bl       #0xe57350 ; ea610094
   0xE3EBAC: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBB0: ldrh     w1, [sp, #0x32] ; e1674079
   0xE3EBB4: bl       #0xe52aa0 ; bb4f0094
   0xE3EBB8: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBBC: ldrh     w1, [sp, #0x34] ; e16b4079
   0xE3EBC0: bl       #0xe56470 ; 2c5e0094
   0xE3EBC4: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBC8: ldrh     w1, [sp, #0x36] ; e16f4079
   0xE3EBCC: bl       #0xe52cc0 ; 3d500094
   0xE3EBD0: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBD4: ldrb     w1, [sp, #0x40] ; e1034139
   0xE3EBD8: bl       #0xe518f0 ; 464b0094
   0xE3EBDC: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBE0: ldrh     w1, [sp, #0x44] ; e18b4079
   0xE3EBE4: bl       #0xe56690 ; ab5e0094
   0xE3EBE8: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBEC: ldrh     w1, [sp, #0x46] ; e18f4079
   0xE3EBF0: bl       #0xe568b0 ; 305f0094
   0xE3EBF4: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBF8: ldrb     w1, [sp, #0x42] ; e10b4139
   0xE3EBFC: bl       #0xe56250 ; 955d0094
   0xE3EC00: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC04: ldrb     w1, [sp, #0x40] ; e1034139
   0xE3EC08: bl       #0xe58650 ; 92660094
   0xE3EC0C: ldr      x21, [x19, #0x70] ; 753a40f9
   0xE3EC10: bl       #0x3f0784 ; ddc6d697
   0xE3EC14: ldrb     w1, [x0, #0x379] ; 01e44d39
   0xE3EC18: mov      x0, x21 ; e00315aa
   0xE3EC1C: bl       #0xe57780 ; d9620094
   0xE3EC20: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC24: ldr      w1, [sp, #0x4c] ; e14f40b9
   0xE3EC28: bl       #0xe53320 ; be510094
   0xE3EC2C: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC30: ldrb     w1, [sp, #0x74] ; e1d34139
   0xE3EC34: bl       #0xe539f0 ; 6f530094
   0xE3EC38: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC3C: mov      w1, #0xff ; e11f8052
   0xE3EC40: bl       #0xe5ae40 ; 80700094
   0xE3EC44: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC48: ldrb     w1, [sp, #0x75] ; e1d74139
   0xE3EC4C: bl       #0xe58430 ; f9650094
   0xE3EC50: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC54: ldrb     w1, [sp, #0x50] ; e1434139
   0xE3EC58: bl       #0xe54f90 ; ce580094
   0xE3EC5C: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC60: ldrb     w1, [sp, #0x52] ; e14b4139
   0xE3EC64: bl       #0xe551a0 ; 4f590094
   0xE3EC68: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC6C: ldrb     w1, [sp, #0x54] ; e1534139
   0xE3EC70: bl       #0xe553b0 ; d0590094
   0xE3EC74: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC78: ldrb     w1, [sp, #0x56] ; e15b4139
   0xE3EC7C: bl       #0xe555c0 ; 515a0094
   0xE3EC80: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC84: ldrb     w1, [sp, #0x58] ; e1634139
~~~

## Static PC 0xE3EBA8 (word 0x940061EA)

- ELF file offset: 0xE3F5F0; opcode: BL; mask: to pid_set (0xE57350)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE3E928: strb     wzr, [sp, #0xa6] ; ff9b0239
   0xE3E92C: strb     w9, [sp, #0x75] ; e9d70139
   0xE3E930: strb     w8, [sp, #0x74] ; e8d30139
   0xE3E934: str      xzr, [sp, #0x38] ; ff1f00f9
   0xE3E938: str      xzr, [sp, #0xd8] ; ff6f00f9
   0xE3E93C: strh     wzr, [sp, #0xe0] ; ffc30179
   0xE3E940: str      x26, [sp, #0x50] ; fa2b00f9
   0xE3E944: str      w26, [sp, #0x58] ; fa5b00b9
   0xE3E948: strh     wzr, [sp, #0xfa] ; fff70179
   0xE3E94C: stur     xzr, [sp, #0x5c] ; ffc305f8
   0xE3E950: stur     xzr, [sp, #0x64] ; ff4306f8
   0xE3E954: strh     wzr, [sp, #0x6c] ; ffdb0079
   0xE3E958: strh     w22, [sp, #0x32] ; f6670079
   0xE3E95C: strh     w21, [sp, #0x40] ; f5830079
   0xE3E960: str      x20, [sp, #0x20] ; f41300f9
   0xE3E964: stp      xzr, xzr, [sp, #0xa8] ; ffff0aa9
   0xE3E968: stp      xzr, xzr, [sp, #0xb8] ; ffff0ba9
   0xE3E96C: stp      xzr, xzr, [sp, #0xc8] ; ffff0ca9
   0xE3E970: stp      xzr, xzr, [sp, #0x78] ; ffff07a9
   0xE3E974: ldr      x8, [x23] ; e80240f9
   0xE3E978: ldr      x8, [x8, #0x10] ; 080940f9
   0xE3E97C: blr      x8 ; 00013fd6
   0xE3E980: mov      x20, x0 ; f40300aa
   0xE3E984: cbz      x0, #0xe3e9dc ; c00200b4
   0xE3E988: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E98C: cmp      x8, #0x10 ; 1f4100f1
   0xE3E990: b.eq     #0xe3eb30 ; 000d0054
   0xE3E994: add      x8, x24, x8, lsl #3 ; 080f088b
   0xE3E998: mov      w21, #0x148 ; 15298052
   0xE3E99C: mov      x0, x20 ; e00314aa
   0xE3E9A0: mov      w1, wzr ; e1031f2a
   0xE3E9A4: mov      x2, x21 ; e20315aa
   0xE3E9A8: str      x23, [x8, #0x18] ; 170d00f9
   0xE3E9AC: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E9B0: add      x8, x8, #1 ; 08050091
   0xE3E9B4: str      x8, [x24, #0x98] ; 084f00f9
   0xE3E9B8: bl       #0x3161520 ; da8a8c94
   0xE3E9BC: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3E9C0: mov      w22, #4 ; 96008052
   0xE3E9C4: sub      x8, x8, #1 ; 080500d1
   0xE3E9C8: str      x8, [x24, #0x98] ; 084f00f9
   0xE3E9CC: ldr      x1, [x25] ; 210340f9
   0xE3E9D0: str      x20, [x25] ; 340300f9
   0xE3E9D4: cbnz     x1, #0xe3e9f4 ; 010100b5
   0xE3E9D8: b        #0xe3ea10 ; 0e000014
   0xE3E9DC: mov      x23, xzr ; f7031faa
   0xE3E9E0: mov      x21, xzr ; f5031faa
   0xE3E9E4: mov      x22, xzr ; f6031faa
   0xE3E9E8: ldr      x1, [x25] ; 210340f9
   0xE3E9EC: str      x20, [x25] ; 340300f9
   0xE3E9F0: cbz      x1, #0xe3ea10 ; 010100b4
   0xE3E9F4: ldr      x0, [x19, #0x38] ; 601e40f9
   0xE3E9F8: cbz      x0, #0xe3ea10 ; c00000b4
   0xE3E9FC: ldr      x8, [x0] ; 080040f9
   0xE3EA00: ldp      x2, x3, [x19, #0x40] ; 620e44a9
   0xE3EA04: ldr      x8, [x8, #0x18] ; 080d40f9
   0xE3EA08: blr      x8 ; 00013fd6
   0xE3EA0C: ldr      x20, [x19, #0x30] ; 741a40f9
   0xE3EA10: mov      w2, #0x148 ; 02298052
   0xE3EA14: mov      x0, x20 ; e00314aa
   0xE3EA18: str      x22, [x19, #0x48] ; 762600f9
   0xE3EA1C: mov      w1, wzr ; e1031f2a
   0xE3EA20: stp      x23, x21, [x19, #0x38] ; 77d603a9
   0xE3EA24: bl       #0x3161520 ; bf8a8c94
   0xE3EA28: ldr      x20, [x19, #8] ; 740640f9
   0xE3EA2C: mov      w1, #0x28 ; 01058052
   0xE3EA30: mov      w2, #8 ; 02018052
   0xE3EA34: ldr      x8, [x20] ; 880240f9
   0xE3EA38: mov      x0, x20 ; e00314aa
   0xE3EA3C: ldr      x8, [x8, #0x10] ; 080940f9
   0xE3EA40: blr      x8 ; 00013fd6
   0xE3EA44: mov      x21, x0 ; f50300aa
   0xE3EA48: cbz      x0, #0xe3ea98 ; 800200b4
   0xE3EA4C: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA50: cmp      x8, #0x10 ; 1f4100f1
   0xE3EA54: b.eq     #0xe3eb30 ; e0060054
   0xE3EA58: add      x8, x24, x8, lsl #3 ; 080f088b
   0xE3EA5C: mov      x0, x21 ; e00315aa
   0xE3EA60: str      x20, [x8, #0x18] ; 140d00f9
   0xE3EA64: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA68: add      x8, x8, #1 ; 08050091
   0xE3EA6C: str      x8, [x24, #0x98] ; 084f00f9
   0xE3EA70: bl       #0xe47564 ; bd220094
   0xE3EA74: ldr      x8, [x24, #0x98] ; 084f40f9
   0xE3EA78: mov      w23, #8 ; 17018052
   0xE3EA7C: sub      x8, x8, #1 ; 080500d1
   0xE3EA80: str      x8, [x24, #0x98] ; 084f00f9
   0xE3EA84: mov      w24, #0x28 ; 18058052
   0xE3EA88: ldr      x22, [x19, #0x70] ; 763a40f9
   0xE3EA8C: str      x21, [x19, #0x70] ; 753a00f9
   0xE3EA90: cbnz     x22, #0xe3eab0 ; 160100b5
   0xE3EA94: b        #0xe3eae4 ; 14000014
   0xE3EA98: mov      x20, xzr ; f4031faa
   0xE3EA9C: mov      x24, xzr ; f8031faa
   0xE3EAA0: mov      x23, xzr ; f7031faa
   0xE3EAA4: ldr      x22, [x19, #0x70] ; 763a40f9
   0xE3EAA8: str      x21, [x19, #0x70] ; 753a00f9
   0xE3EAAC: cbz      x22, #0xe3eae4 ; d60100b4
   0xE3EAB0: ldr      x8, [x19, #0x78] ; 683e40f9
   0xE3EAB4: cbz      x8, #0xe3eae4 ; 880100b4
   0xE3EAB8: ldr      x8, [x22] ; c80240f9
   0xE3EABC: mov      x0, x22 ; e00316aa
   0xE3EAC0: ldr      x8, [x8] ; 080140f9
   0xE3EAC4: blr      x8 ; 00013fd6
   0xE3EAC8: ldp      x0, x2, [x19, #0x78] ; 608a47a9
   0xE3EACC: mov      x1, x22 ; e10316aa
   0xE3EAD0: ldr      x3, [x19, #0x88] ; 634640f9
   0xE3EAD4: ldr      x8, [x0] ; 080040f9
   0xE3EAD8: ldr      x8, [x8, #0x18] ; 080d40f9
   0xE3EADC: blr      x8 ; 00013fd6
   0xE3EAE0: ldr      x21, [x19, #0x70] ; 753a40f9
   0xE3EAE4: ldr      x1, [x19, #0x30] ; 611a40f9
   0xE3EAE8: mov      x0, x21 ; e00315aa
   0xE3EAEC: mov      x2, xzr ; e2031faa
   0xE3EAF0: stp      x20, x24, [x19, #0x78] ; 74e207a9
   0xE3EAF4: str      x23, [x19, #0x88] ; 774600f9
   0xE3EAF8: bl       #0xe475fc ; c1220094
   0xE3EAFC: add      x1, sp, #8 ; e1230091
   0xE3EB00: mov      x0, x19 ; e00313aa
   0xE3EB04: bl       #0xe3eb34 ; 0c000094
   0xE3EB08: mov      x0, x19 ; e00313aa
   0xE3EB0C: bl       #0xe3f18c ; a0010094
   0xE3EB10: ldp      x20, x19, [sp, #0x150] ; f44f55a9
   0xE3EB14: ldp      x22, x21, [sp, #0x140] ; f65754a9
   0xE3EB18: ldp      x24, x23, [sp, #0x130] ; f85f53a9
   0xE3EB1C: ldp      x26, x25, [sp, #0x120] ; fa6752a9
   0xE3EB20: ldp      x28, x27, [sp, #0x110] ; fc6f51a9
   0xE3EB24: ldp      x29, x30, [sp, #0x100] ; fd7b50a9
   0xE3EB28: add      sp, sp, #0x160 ; ff830591
   0xE3EB2C: ret       ; c0035fd6
   0xE3EB30: bl       #0x2fa70 ; d0c3c797
   0xE3EB34: ldrh     w8, [x1, #0x2a] ; 28544079
   0xE3EB38: cbz      w8, #0xe3f188 ; 88320034
   0xE3EB3C: sub      sp, sp, #0x140 ; ff0305d1
   0xE3EB40: stp      x29, x30, [sp, #0x100] ; fd7b10a9
   0xE3EB44: str      x28, [sp, #0x110] ; fc8b00f9
   0xE3EB48: stp      x22, x21, [sp, #0x120] ; f65712a9
   0xE3EB4C: stp      x20, x19, [sp, #0x130] ; f44f13a9
   0xE3EB50: add      x29, sp, #0x100 ; fd030491
   0xE3EB54: mov      x19, x0 ; f30300aa
   0xE3EB58: add      x0, sp, #8 ; e0230091
   0xE3EB5C: bl       #0xbef804 ; 2ac3f697
   0xE3EB60: add      x0, sp, #8 ; e0230091
   0xE3EB64: bl       #0x656f80 ; 0761e097
   0xE3EB68: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB6C: bl       #0xe47a14 ; aa230094
   0xE3EB70: mov      w20, w0 ; f403002a
   0xE3EB74: tbnz     w0, #0, #0xe3eb80 ; 60000037
   0xE3EB78: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB7C: bl       #0xe480e0 ; 59250094
   0xE3EB80: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB84: bl       #0xe483c0 ; 0f260094
   0xE3EB88: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB8C: ldr      w1, [sp, #0x18] ; e11b40b9
   0xE3EB90: bl       #0xe514d0 ; 504a0094
   0xE3EB94: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EB98: ldr      w1, [sp, #0x20] ; e12340b9
   0xE3EB9C: bl       #0xe52ee0 ; d1500094
   0xE3EBA0: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBA4: ldr      w1, [sp, #0x28] ; e12b40b9
>> 0xE3EBA8: bl       #0xe57350 ; ea610094
   0xE3EBAC: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBB0: ldrh     w1, [sp, #0x32] ; e1674079
   0xE3EBB4: bl       #0xe52aa0 ; bb4f0094
   0xE3EBB8: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBBC: ldrh     w1, [sp, #0x34] ; e16b4079
   0xE3EBC0: bl       #0xe56470 ; 2c5e0094
   0xE3EBC4: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBC8: ldrh     w1, [sp, #0x36] ; e16f4079
   0xE3EBCC: bl       #0xe52cc0 ; 3d500094
   0xE3EBD0: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBD4: ldrb     w1, [sp, #0x40] ; e1034139
   0xE3EBD8: bl       #0xe518f0 ; 464b0094
   0xE3EBDC: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBE0: ldrh     w1, [sp, #0x44] ; e18b4079
   0xE3EBE4: bl       #0xe56690 ; ab5e0094
   0xE3EBE8: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBEC: ldrh     w1, [sp, #0x46] ; e18f4079
   0xE3EBF0: bl       #0xe568b0 ; 305f0094
   0xE3EBF4: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EBF8: ldrb     w1, [sp, #0x42] ; e10b4139
   0xE3EBFC: bl       #0xe56250 ; 955d0094
   0xE3EC00: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC04: ldrb     w1, [sp, #0x40] ; e1034139
   0xE3EC08: bl       #0xe58650 ; 92660094
   0xE3EC0C: ldr      x21, [x19, #0x70] ; 753a40f9
   0xE3EC10: bl       #0x3f0784 ; ddc6d697
   0xE3EC14: ldrb     w1, [x0, #0x379] ; 01e44d39
   0xE3EC18: mov      x0, x21 ; e00315aa
   0xE3EC1C: bl       #0xe57780 ; d9620094
   0xE3EC20: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC24: ldr      w1, [sp, #0x4c] ; e14f40b9
   0xE3EC28: bl       #0xe53320 ; be510094
   0xE3EC2C: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC30: ldrb     w1, [sp, #0x74] ; e1d34139
   0xE3EC34: bl       #0xe539f0 ; 6f530094
   0xE3EC38: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC3C: mov      w1, #0xff ; e11f8052
   0xE3EC40: bl       #0xe5ae40 ; 80700094
   0xE3EC44: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC48: ldrb     w1, [sp, #0x75] ; e1d74139
   0xE3EC4C: bl       #0xe58430 ; f9650094
   0xE3EC50: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC54: ldrb     w1, [sp, #0x50] ; e1434139
   0xE3EC58: bl       #0xe54f90 ; ce580094
   0xE3EC5C: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC60: ldrb     w1, [sp, #0x52] ; e14b4139
   0xE3EC64: bl       #0xe551a0 ; 4f590094
   0xE3EC68: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC6C: ldrb     w1, [sp, #0x54] ; e1534139
   0xE3EC70: bl       #0xe553b0 ; d0590094
   0xE3EC74: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC78: ldrb     w1, [sp, #0x56] ; e15b4139
   0xE3EC7C: bl       #0xe555c0 ; 515a0094
   0xE3EC80: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC84: ldrb     w1, [sp, #0x58] ; e1634139
   0xE3EC88: bl       #0xe557d0 ; d25a0094
   0xE3EC8C: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC90: ldrb     w1, [sp, #0x5a] ; e16b4139
   0xE3EC94: bl       #0xe559e0 ; 535b0094
   0xE3EC98: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3EC9C: ldrb     w1, [sp, #0x5c] ; e1734139
   0xE3ECA0: bl       #0xe53c10 ; dc530094
   0xE3ECA4: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3ECA8: ldrb     w1, [sp, #0x5e] ; e17b4139
   0xE3ECAC: bl       #0xe53e30 ; 61540094
   0xE3ECB0: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3ECB4: ldrb     w1, [sp, #0x60] ; e1834139
   0xE3ECB8: bl       #0xe54050 ; e6540094
   0xE3ECBC: ldr      x0, [x19, #0x70] ; 603a40f9
   0xE3ECC0: ldrb     w1, [sp, #0x62] ; e18b4139
   0xE3ECC4: bl       #0xe54270 ; 6b550094
   0xE3ECC8: ldr      x0, [x19, #0x70] ; 603a40f9
~~~

