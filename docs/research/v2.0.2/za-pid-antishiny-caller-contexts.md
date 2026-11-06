# Z-A v2.0.2 AntiShiny and PID generator callers exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 6
- Instruction window: 0x120 bytes before and 0x120 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0x55BD9C (word 0x94240513)

- ELF file offset: 0x55C7E4; opcode: BL; mask: to shiny_xor_check (0xE5D1E8)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
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

## Static PC 0x657124 (word 0x94201831)

- ELF file offset: 0x657B6C; opcode: BL; mask: to shiny_xor_check (0xE5D1E8)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
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

