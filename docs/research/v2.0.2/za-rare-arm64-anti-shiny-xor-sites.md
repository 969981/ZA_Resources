# Z-A v2.0.2 AntiShiny XOR 0x10000000 exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 3
- Instruction window: 0xC0 bytes before and 0xC0 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0xE5D20C (word 0x52040029)

- ELF file offset: 0xE5DC54; opcode: EOR; mask: 0x10000000
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE5D14C: umull    x9, w12, w9 ; 897da99b
   0xE5D150: lsr      x9, x9, #0x20 ; 29fd60d3
   0xE5D154: lsr      x11, x11, #0x20 ; 6bfd60d3
   0xE5D158: csel     w8, w8, w9, ne ; 0811891a
   0xE5D15C: cmn      w10, #1 ; 5f050031
   0xE5D160: csel     w0, w11, w8, eq ; 6001881a
   0xE5D164: ret       ; c0035fd6
   0xE5D168: and      w9, w1, #0xffff ; 293c0012
   0xE5D16C: and      w8, w3, #0xfffc ; 68341e12
   0xE5D170: and      w10, w4, #0xffff ; 8a3c0012
   0xE5D174: lsl      w9, w9, #1 ; 29791f53
   0xE5D178: add      x10, x10, w10, uxtw #2 ; 4a492a8b
   0xE5D17C: add      w9, w9, w2, uxth ; 2921220b
   0xE5D180: adrp     x11, #0x3303000 ; 2b2501d0
   0xE5D184: add      x11, x11, #0xb30 ; 6bc12c91
   0xE5D188: add      w8, w9, w8, lsr #2 ; 2809480b
   0xE5D18C: and      w9, w0, #0xff ; 091c0012
   0xE5D190: add      x10, x11, x10 ; 6a010a8b
   0xE5D194: mov      w11, #0x5a ; 4b0b8052
   0xE5D198: mov      w12, #0x6e ; cc0d8052
   0xE5D19C: ldrsb    w10, [x10, #4] ; 4a11c039
   0xE5D1A0: mul      w8, w8, w9 ; 087d091b
   0xE5D1A4: mov      w9, #0x5c29 ; 29858b52
   0xE5D1A8: movk     w9, #0x28f, lsl #16 ; e951a072
   0xE5D1AC: cmp      w10, #1 ; 5f050071
   0xE5D1B0: umull    x8, w8, w9 ; 087da99b
   0xE5D1B4: lsr      x8, x8, #0x20 ; 08fd60d3
   0xE5D1B8: add      w8, w8, #5 ; 08150011
   0xE5D1BC: and      w8, w8, #0xffff ; 083d0012
   0xE5D1C0: mul      w11, w8, w11 ; 0b7d0b1b
   0xE5D1C4: mul      w12, w8, w12 ; 0c7d0c1b
   0xE5D1C8: umull    x11, w11, w9 ; 6b7da99b
   0xE5D1CC: umull    x9, w12, w9 ; 897da99b
   0xE5D1D0: lsr      x9, x9, #0x20 ; 29fd60d3
   0xE5D1D4: lsr      x11, x11, #0x20 ; 6bfd60d3
   0xE5D1D8: csel     w8, w8, w9, ne ; 0811891a
   0xE5D1DC: cmn      w10, #1 ; 5f050031
   0xE5D1E0: csel     w0, w11, w8, eq ; 6001881a
   0xE5D1E4: ret       ; c0035fd6
   0xE5D1E8: eor      w8, w1, w0 ; 2800004a
   0xE5D1EC: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D1F0: eor      w8, w9, w8, lsr #16 ; 2841484a
   0xE5D1F4: cmp      w8, #0x10 ; 1f410071
   0xE5D1F8: cset     w0, lo ; e0279f1a
   0xE5D1FC: ret       ; c0035fd6
   0xE5D200: eor      w8, w1, w0 ; 2800004a
   0xE5D204: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D208: eor      w8, w9, w8, lsr #16 ; 2841484a
>> 0xE5D20C: eor      w9, w1, #0x10000000 ; 29000452
   0xE5D210: cmp      w8, #0x10 ; 1f410071
   0xE5D214: csel     w0, w9, w1, lo ; 2031811a
   0xE5D218: ret       ; c0035fd6
   0xE5D21C: eor      w8, w1, w0 ; 2800004a
   0xE5D220: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D224: eor      w8, w9, w8, lsr #16 ; 2841484a
   0xE5D228: mov      w9, w1 ; e903012a
   0xE5D22C: cmp      w8, #0x10 ; 1f410071
   0xE5D230: eor      w8, w0, w0, lsr #16 ; 0840404a
   0xE5D234: eor      w8, w8, w1 ; 0801014a
   0xE5D238: bfi      w9, w8, #0x10, #0x10 ; 093d1033
   0xE5D23C: csel     w0, w1, w9, lo ; 2030891a
   0xE5D240: ret       ; c0035fd6
   0xE5D244: eor      w8, w1, w0 ; 2800004a
   0xE5D248: lsr      w9, w8, #0x10 ; 097d1053
   0xE5D24C: and      w10, w8, #0xfff0 ; 0a2d1c12
   0xE5D250: cmp      w9, w8, uxth ; 3f21286b
   0xE5D254: eor      w10, w10, w9 ; 4a01094a
   0xE5D258: cset     w8, eq ; e8179f1a
   0xE5D25C: cmp      w2, #0x22 ; 5f880071
   0xE5D260: cset     w9, eq ; e9179f1a
   0xE5D264: orr      w9, w9, w3 ; 2901032a
   0xE5D268: orr      w8, w9, w8 ; 2801082a
   0xE5D26C: tst      w8, #1 ; 1f010072
   0xE5D270: mov      w8, #1 ; 28008052
   0xE5D274: cinc     w8, w8, ne ; 0805881a
   0xE5D278: cmp      w10, #0x10 ; 5f410071
   0xE5D27C: csel     w0, w8, wzr, lo ; 00319f1a
   0xE5D280: ret       ; c0035fd6
   0xE5D284: tst      w2, #0xff ; 5f1c0072
   0xE5D288: b.eq     #0xe5d2b0 ; 40010054
   0xE5D28C: eor      w8, w0, w0, lsr #16 ; 0840404a
   0xE5D290: and      w9, w2, #0xff ; 491c0012
   0xE5D294: cmp      w9, #1 ; 3f050071
   0xE5D298: cset     w9, eq ; e9179f1a
   0xE5D29C: eor      w8, w8, w1 ; 0801014a
   0xE5D2A0: eor      w8, w8, w9 ; 0801094a
   0xE5D2A4: bfi      w1, w8, #0x10, #0x10 ; 013d1033
   0xE5D2A8: mov      w0, w1 ; e003012a
   0xE5D2AC: ret       ; c0035fd6
   0xE5D2B0: eor      w8, w1, w0 ; 2800004a
   0xE5D2B4: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D2B8: eor      w8, w9, w8, lsr #16 ; 2841484a
   0xE5D2BC: eor      w9, w1, #0x10000000 ; 29000452
   0xE5D2C0: cmp      w8, #0x10 ; 1f410071
   0xE5D2C4: csel     w0, w9, w1, lo ; 2031811a
   0xE5D2C8: ret       ; c0035fd6
   0xE5D2CC: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
~~~

## Static PC 0xE5D2BC (word 0x52040029)

- ELF file offset: 0xE5DD04; opcode: EOR; mask: 0x10000000
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE5D1FC: ret       ; c0035fd6
   0xE5D200: eor      w8, w1, w0 ; 2800004a
   0xE5D204: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D208: eor      w8, w9, w8, lsr #16 ; 2841484a
   0xE5D20C: eor      w9, w1, #0x10000000 ; 29000452
   0xE5D210: cmp      w8, #0x10 ; 1f410071
   0xE5D214: csel     w0, w9, w1, lo ; 2031811a
   0xE5D218: ret       ; c0035fd6
   0xE5D21C: eor      w8, w1, w0 ; 2800004a
   0xE5D220: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D224: eor      w8, w9, w8, lsr #16 ; 2841484a
   0xE5D228: mov      w9, w1 ; e903012a
   0xE5D22C: cmp      w8, #0x10 ; 1f410071
   0xE5D230: eor      w8, w0, w0, lsr #16 ; 0840404a
   0xE5D234: eor      w8, w8, w1 ; 0801014a
   0xE5D238: bfi      w9, w8, #0x10, #0x10 ; 093d1033
   0xE5D23C: csel     w0, w1, w9, lo ; 2030891a
   0xE5D240: ret       ; c0035fd6
   0xE5D244: eor      w8, w1, w0 ; 2800004a
   0xE5D248: lsr      w9, w8, #0x10 ; 097d1053
   0xE5D24C: and      w10, w8, #0xfff0 ; 0a2d1c12
   0xE5D250: cmp      w9, w8, uxth ; 3f21286b
   0xE5D254: eor      w10, w10, w9 ; 4a01094a
   0xE5D258: cset     w8, eq ; e8179f1a
   0xE5D25C: cmp      w2, #0x22 ; 5f880071
   0xE5D260: cset     w9, eq ; e9179f1a
   0xE5D264: orr      w9, w9, w3 ; 2901032a
   0xE5D268: orr      w8, w9, w8 ; 2801082a
   0xE5D26C: tst      w8, #1 ; 1f010072
   0xE5D270: mov      w8, #1 ; 28008052
   0xE5D274: cinc     w8, w8, ne ; 0805881a
   0xE5D278: cmp      w10, #0x10 ; 5f410071
   0xE5D27C: csel     w0, w8, wzr, lo ; 00319f1a
   0xE5D280: ret       ; c0035fd6
   0xE5D284: tst      w2, #0xff ; 5f1c0072
   0xE5D288: b.eq     #0xe5d2b0 ; 40010054
   0xE5D28C: eor      w8, w0, w0, lsr #16 ; 0840404a
   0xE5D290: and      w9, w2, #0xff ; 491c0012
   0xE5D294: cmp      w9, #1 ; 3f050071
   0xE5D298: cset     w9, eq ; e9179f1a
   0xE5D29C: eor      w8, w8, w1 ; 0801014a
   0xE5D2A0: eor      w8, w8, w9 ; 0801094a
   0xE5D2A4: bfi      w1, w8, #0x10, #0x10 ; 013d1033
   0xE5D2A8: mov      w0, w1 ; e003012a
   0xE5D2AC: ret       ; c0035fd6
   0xE5D2B0: eor      w8, w1, w0 ; 2800004a
   0xE5D2B4: and      w9, w8, #0xfff0 ; 092d1c12
   0xE5D2B8: eor      w8, w9, w8, lsr #16 ; 2841484a
>> 0xE5D2BC: eor      w9, w1, #0x10000000 ; 29000452
   0xE5D2C0: cmp      w8, #0x10 ; 1f410071
   0xE5D2C4: csel     w0, w9, w1, lo ; 2031811a
   0xE5D2C8: ret       ; c0035fd6
   0xE5D2CC: stp      x29, x30, [sp, #-0x20]! ; fd7bbea9
   0xE5D2D0: stp      x20, x19, [sp, #0x10] ; f44f01a9
   0xE5D2D4: mov      x29, sp ; fd030091
   0xE5D2D8: mov      w19, w2 ; f303022a
   0xE5D2DC: and      w20, w2, #0xff ; 541c0012
   0xE5D2E0: bl       #0x83fd88 ; aa8ae797
   0xE5D2E4: cmp      w20, #2 ; 9f0a0071
   0xE5D2E8: sub      w8, w0, #1 ; 08040051
   0xE5D2EC: csel     w10, wzr, w19, eq ; ea03931a
   0xE5D2F0: ldp      x20, x19, [sp, #0x10] ; f44f41a9
   0xE5D2F4: and      w9, w8, #0xff ; 091d0012
   0xE5D2F8: cmp      w9, #3 ; 3f0d0071
   0xE5D2FC: csel     w0, w8, w10, lo ; 00318a1a
   0xE5D300: ldp      x29, x30, [sp], #0x20 ; fd7bc2a8
   0xE5D304: ret       ; c0035fd6
   0xE5D308: cmp      w0, #0x19 ; 1f640071
   0xE5D30C: mov      w9, #0x6b5d ; a96b8d52
   0xE5D310: movk     w9, #0x148, lsl #16 ; 0929a072
   0xE5D314: cset     w8, lo ; e8279f1a
   0xE5D318: lsr      w9, w9, w0 ; 2925c01a
   0xE5D31C: and      w0, w8, w9 ; 0001090a
   0xE5D320: ret       ; c0035fd6
   0xE5D324: cmp      w0, #0x18 ; 1f600071
   0xE5D328: mov      w9, #0x94a2 ; 49949252
   0xE5D32C: movk     w9, #0xb7, lsl #16 ; e916a072
   0xE5D330: cset     w8, lo ; e8279f1a
   0xE5D334: lsr      w9, w9, w0 ; 2925c01a
   0xE5D338: and      w0, w8, w9 ; 0001090a
   0xE5D33C: ret       ; c0035fd6
   0xE5D340: mov      w8, #0xd ; a8018052
   0xE5D344: strb     w8, [x0] ; 08000039
   0xE5D348: adrp     x0, #0x3303000 ; 202501d0
   0xE5D34C: add      x0, x0, #0xbb0 ; 00c02e91
   0xE5D350: ret       ; c0035fd6
   0xE5D354: mov      w8, #0xc ; 88018052
   0xE5D358: strb     w8, [x0] ; 08000039
   0xE5D35C: adrp     x0, #0x3303000 ; 202501d0
   0xE5D360: add      x0, x0, #0xbe4 ; 00902f91
   0xE5D364: ret       ; c0035fd6
   0xE5D368: and      w8, w2, #0xff ; 481c0012
   0xE5D36C: cmp      w8, #1 ; 1f050071
   0xE5D370: b.eq     #0xe5d380 ; 80000054
   0xE5D374: cmp      w8, #2 ; 1f090071
   0xE5D378: b.ne     #0xe5d384 ; 61000054
   0xE5D37C: b        #0xe3419c ; 885bff17
~~~

## Static PC 0x2138DC0 (word 0x5204018C)

- ELF file offset: 0x2139808; opcode: EOR; mask: 0x10000000
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x2138D00: stp      w12, w14, [x2, #0x48] ; 4c380929
   0x2138D04: eor      w17, w17, w15 ; 31020f4a
   0x2138D08: stp      w18, w15, [x2, #0x50] ; 523c0a29
   0x2138D0C: eor      w16, w17, w16 ; 3002104a
   0x2138D10: ubfx     w1, w16, #8, #8 ; 013e0853
   0x2138D14: ubfx     w18, w16, #0x10, #8 ; 125e1053
   0x2138D18: stp      w17, w16, [x2, #0x58] ; 51400b29
   0x2138D1C: add      x1, x10, w1, uxtw #2 ; 4149218b
   0x2138D20: add      x18, x9, w18, uxtw #2 ; 3249328b
   0x2138D24: ldrb     w1, [x1, #2] ; 21084039
   0x2138D28: ldrb     w18, [x18, #3] ; 520e4039
   0x2138D2C: lsl      w1, w1, #0x10 ; 213c1053
   0x2138D30: orr      w18, w1, w18, lsl #24 ; 3260122a
   0x2138D34: and      w1, w16, #0xff ; 011e0012
   0x2138D38: add      x1, x11, w1, uxtw #2 ; 6149218b
   0x2138D3C: ldrb     w1, [x1, #1] ; 21044039
   0x2138D40: orr      w18, w18, w1, lsl #8 ; 5222012a
   0x2138D44: lsr      w1, w16, #0x18 ; 017e1853
   0x2138D48: ubfiz    x1, x1, #2, #0x20 ; 217c7ed3
   0x2138D4C: ldrb     w1, [x8, x1] ; 01696138
   0x2138D50: orr      w18, w18, w1 ; 5202012a
   0x2138D54: eor      w12, w18, w12 ; 4c020c4a
   0x2138D58: eor      w12, w12, #0x8000000 ; 8c010552
   0x2138D5C: eor      w13, w13, w12 ; ad010c4a
   0x2138D60: eor      w14, w14, w12 ; ce010c4a
   0x2138D64: eor      w18, w15, w13 ; f2010d4a
   0x2138D68: stp      w12, w14, [x2, #0x60] ; 4c380c29
   0x2138D6C: eor      w17, w17, w18 ; 3102124a
   0x2138D70: stp      w13, w18, [x2, #0x68] ; 4d480d29
   0x2138D74: eor      w16, w17, w16 ; 3002104a
   0x2138D78: ubfx     w1, w16, #8, #8 ; 013e0853
   0x2138D7C: ubfx     w18, w16, #0x10, #8 ; 125e1053
   0x2138D80: stp      w17, w16, [x2, #0x70] ; 51400e29
   0x2138D84: add      x1, x10, w1, uxtw #2 ; 4149218b
   0x2138D88: add      x18, x9, w18, uxtw #2 ; 3249328b
   0x2138D8C: ldrb     w1, [x1, #2] ; 21084039
   0x2138D90: ldrb     w18, [x18, #3] ; 520e4039
   0x2138D94: lsl      w1, w1, #0x10 ; 213c1053
   0x2138D98: orr      w18, w1, w18, lsl #24 ; 3260122a
   0x2138D9C: and      w1, w16, #0xff ; 011e0012
   0x2138DA0: add      x1, x11, w1, uxtw #2 ; 6149218b
   0x2138DA4: ldrb     w1, [x1, #1] ; 21044039
   0x2138DA8: orr      w18, w18, w1, lsl #8 ; 5222012a
   0x2138DAC: lsr      w1, w16, #0x18 ; 017e1853
   0x2138DB0: ubfiz    x1, x1, #2, #0x20 ; 217c7ed3
   0x2138DB4: ldrb     w1, [x8, x1] ; 01696138
   0x2138DB8: orr      w18, w18, w1 ; 5202012a
   0x2138DBC: eor      w12, w18, w12 ; 4c020c4a
>> 0x2138DC0: eor      w12, w12, #0x10000000 ; 8c010452
   0x2138DC4: eor      w14, w14, w12 ; ce010c4a
   0x2138DC8: eor      w15, w15, w14 ; ef010e4a
   0x2138DCC: eor      w18, w13, w14 ; b2010e4a
   0x2138DD0: stp      w12, w14, [x2, #0x78] ; 4c380f29
   0x2138DD4: eor      w17, w17, w15 ; 31020f4a
   0x2138DD8: stp      w18, w15, [x2, #0x80] ; 523c1029
   0x2138DDC: eor      w16, w17, w16 ; 3002104a
   0x2138DE0: ubfx     w1, w16, #8, #8 ; 013e0853
   0x2138DE4: ubfx     w18, w16, #0x10, #8 ; 125e1053
   0x2138DE8: stp      w17, w16, [x2, #0x88] ; 51401129
   0x2138DEC: add      x1, x10, w1, uxtw #2 ; 4149218b
   0x2138DF0: add      x18, x9, w18, uxtw #2 ; 3249328b
   0x2138DF4: ldrb     w1, [x1, #2] ; 21084039
   0x2138DF8: ldrb     w18, [x18, #3] ; 520e4039
   0x2138DFC: lsl      w1, w1, #0x10 ; 213c1053
   0x2138E00: orr      w18, w1, w18, lsl #24 ; 3260122a
   0x2138E04: and      w1, w16, #0xff ; 011e0012
   0x2138E08: add      x1, x11, w1, uxtw #2 ; 6149218b
   0x2138E0C: ldrb     w1, [x1, #1] ; 21044039
   0x2138E10: orr      w18, w18, w1, lsl #8 ; 5222012a
   0x2138E14: lsr      w1, w16, #0x18 ; 017e1853
   0x2138E18: ubfiz    x1, x1, #2, #0x20 ; 217c7ed3
   0x2138E1C: ldrb     w1, [x8, x1] ; 01696138
   0x2138E20: orr      w18, w18, w1 ; 5202012a
   0x2138E24: eor      w12, w18, w12 ; 4c020c4a
   0x2138E28: eor      w12, w12, #0x20000000 ; 8c010352
   0x2138E2C: eor      w13, w13, w12 ; ad010c4a
   0x2138E30: eor      w14, w14, w12 ; ce010c4a
   0x2138E34: eor      w18, w15, w13 ; f2010d4a
   0x2138E38: stp      w12, w14, [x2, #0x90] ; 4c381229
   0x2138E3C: eor      w17, w17, w18 ; 3102124a
   0x2138E40: stp      w13, w18, [x2, #0x98] ; 4d481329
   0x2138E44: eor      w16, w17, w16 ; 3002104a
   0x2138E48: ubfx     w1, w16, #8, #8 ; 013e0853
   0x2138E4C: ubfx     w18, w16, #0x10, #8 ; 125e1053
   0x2138E50: stp      w17, w16, [x2, #0xa0] ; 51401429
   0x2138E54: add      x1, x10, w1, uxtw #2 ; 4149218b
   0x2138E58: add      x18, x9, w18, uxtw #2 ; 3249328b
   0x2138E5C: ldrb     w1, [x1, #2] ; 21084039
   0x2138E60: ldrb     w18, [x18, #3] ; 520e4039
   0x2138E64: lsl      w1, w1, #0x10 ; 213c1053
   0x2138E68: orr      w18, w1, w18, lsl #24 ; 3260122a
   0x2138E6C: and      w1, w16, #0xff ; 011e0012
   0x2138E70: add      x1, x11, w1, uxtw #2 ; 6149218b
   0x2138E74: ldrb     w1, [x1, #1] ; 21044039
   0x2138E78: orr      w18, w18, w1, lsl #8 ; 5222012a
   0x2138E7C: lsr      w1, w16, #0x18 ; 017e1853
   0x2138E80: ubfiz    x1, x1, #2, #0x20 ; 217c7ed3
~~~

