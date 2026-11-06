# Z-A v2.0.2 Inputs to native shiny-mode state builder 0x656060 exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 5
- Instruction window: 0x200 bytes before and 0x80 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0x49CCA4 (word 0x9406E4EF)

- ELF file offset: 0x49D6EC; opcode: BL; mask: to native_pid_state_builder (0x656060)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x49CAA4: dup      v1.4s, v1.s[2] ; 2104144e
   0x49CAA8: fmul     v2.4s, v5.4s, v2.4s ; a2dc226e
   0x49CAAC: mov      v1.s[1], v0.s[2] ; 01440c6e
   0x49CAB0: fmul     v0.4s, v3.4s, v4.4s ; 60dc246e
   0x49CAB4: fmul     v1.4s, v1.4s, v2.4s ; 21dc226e
   0x49CAB8: fmla     v1.4s, v6.4s, v0.4s ; c1cc204e
   0x49CABC: ldr      q0, [sp, #0x30] ; e00fc03d
   0x49CAC0: str      q0, [sp, #0x70] ; e01f803d
   0x49CAC4: str      q1, [sp, #0x50] ; e117803d
   0x49CAC8: bl       #0x29567c0 ; 3ee79294
   0x49CACC: add      x8, sp, #0x50 ; e8430191
   0x49CAD0: bl       #0x8fa750 ; 20771194
   0x49CAD4: ldr      x0, [sp, #0x50] ; e02b40f9
   0x49CAD8: add      x8, sp, #0x70 ; e8c30191
   0x49CADC: bl       #0x89c7d0 ; 3dff0f94
   0x49CAE0: add      x8, sp, #0x48 ; e8230191
   0x49CAE4: add      x0, sp, #0x70 ; e0c30191
   0x49CAE8: bl       #0xc86f0 ; 02aff097
   0x49CAEC: ldr      x0, [sp, #0x48] ; e02740f9
   0x49CAF0: cbz      x0, #0x49cafc ; 600000b4
   0x49CAF4: movi     d0, #0000000000000000 ; 00e4002f
   0x49CAF8: bl       #0x9e8c60 ; 5a301594
   0x49CAFC: add      x0, sp, #0x48 ; e0230191
   0x49CB00: bl       #0xada50 ; d443f097
   0x49CB04: add      x0, sp, #0x50 ; e0430191
   0x49CB08: bl       #0xacd50 ; 9240f097
   0x49CB0C: ldur     x0, [x29, #-0x48] ; a0835bf8
   0x49CB10: cbnz     x0, #0x49cb3c ; 600100b5
   0x49CB14: add      x0, x29, #0x18 ; a0630091
   0x49CB18: bl       #0x6a3f60 ; 121d0894
   0x49CB1C: ldp      d9, d8, [sp, #0xd0] ; e9234d6d
   0x49CB20: ldr      x19, [sp, #0xf0] ; f37b40f9
   0x49CB24: ldp      d11, d10, [sp, #0xc0] ; eb2b4c6d
   0x49CB28: ldp      d13, d12, [sp, #0xb0] ; ed334b6d
   0x49CB2C: ldp      d15, d14, [sp, #0xa0] ; ef3b4a6d
   0x49CB30: ldp      x29, x30, [sp, #0xe0] ; fd7b4ea9
   0x49CB34: add      sp, sp, #0x100 ; ff030491
   0x49CB38: ret       ; c0035fd6
   0x49CB3C: ldr      x8, [x0] ; 080040f9
   0x49CB40: ldr      x8, [x8, #0x60] ; 083140f9
   0x49CB44: blr      x8 ; 00013fd6
   0x49CB48: b        #0x49cb14 ; f3ffff17
   0x49CB4C: adrp     x8, #0x3f24000 ; 48d40190
   0x49CB50: add      x8, x8, #0xac0 ; 08012b91
   0x49CB54: ldr      x0, [x8] ; 000140f9
   0x49CB58: b        #0x49c494 ; 4ffeff17
   0x49CB5C: adrp     x8, #0x3f24000 ; 48d40190
   0x49CB60: add      x8, x8, #0xac0 ; 08012b91
   0x49CB64: ldr      x0, [x8] ; 000140f9
   0x49CB68: b        #0x49c4c0 ; 56feff17
   0x49CB6C: adrp     x8, #0x3f24000 ; 48d40190
   0x49CB70: add      x8, x8, #0xac0 ; 08012b91
   0x49CB74: ldr      x0, [x8] ; 000140f9
   0x49CB78: b        #0x49c4ec ; 5dfeff17
   0x49CB7C: adrp     x8, #0x3f24000 ; 48d40190
   0x49CB80: add      x8, x8, #0xac0 ; 08012b91
   0x49CB84: ldr      x0, [x8] ; 000140f9
   0x49CB88: b        #0x49c518 ; 64feff17
   0x49CB8C: sub      sp, sp, #0x1d0 ; ff4307d1
   0x49CB90: stp      x29, x30, [sp, #0x180] ; fd7b18a9
   0x49CB94: stp      x28, x25, [sp, #0x190] ; fc6719a9
   0x49CB98: stp      x24, x23, [sp, #0x1a0] ; f85f1aa9
   0x49CB9C: stp      x22, x21, [sp, #0x1b0] ; f6571ba9
   0x49CBA0: stp      x20, x19, [sp, #0x1c0] ; f44f1ca9
   0x49CBA4: add      x29, sp, #0x180 ; fd030691
   0x49CBA8: add      x8, sp, #0x10 ; e8430091
   0x49CBAC: mov      x19, x0 ; f30300aa
   0x49CBB0: bl       #0x511f84 ; f5d40194
   0x49CBB4: ldr      x0, [sp, #0x10] ; e00b40f9
   0x49CBB8: sub      x8, x29, #0x10 ; a84300d1
   0x49CBBC: bl       #0x514fe0 ; 09e10194
   0x49CBC0: add      x0, sp, #0x10 ; e0430091
   0x49CBC4: bl       #0x5120c0 ; 3fd50194
   0x49CBC8: adrp     x8, #0x610d000 ; 88e302b0
   0x49CBCC: add      x8, x8, #0x500 ; 08011491
   0x49CBD0: ldr      w8, [x8, #0x180] ; 088141b9
   0x49CBD4: dmb      ishld ; bf3903d5
   0x49CBD8: cbz      w8, #0x49cde4 ; 68100034
   0x49CBDC: sub      x0, x29, #0x10 ; a04300d1
   0x49CBE0: bl       #0xbf9740 ; d8721d94
   0x49CBE4: tbnz     w0, #0, #0x49cde4 ; 00100037
   0x49CBE8: sub      x8, x29, #0x20 ; a88300d1
   0x49CBEC: sub      x0, x29, #0x10 ; a04300d1
   0x49CBF0: bl       #0x514e5c ; 9be00194
   0x49CBF4: adrp     x0, #0x3ec6000 ; 40d101d0
   0x49CBF8: ldur     x20, [x29, #-0x20] ; b4035ef8
   0x49CBFC: add      x8, sp, #0x10 ; e8430091
   0x49CC00: ldr      x0, [x0, #0xdc8] ; 00e446f9
   0x49CC04: bl       #0x421c ; 869ded97
   0x49CC08: add      x0, x19, #0x10 ; 60420091
   0x49CC0C: sub      x8, x29, #0xa8 ; a8a302d1
   0x49CC10: bl       #0x38b90 ; e06fee97
   0x49CC14: ldr      x8, [x20] ; 880240f9
   0x49CC18: add      x1, sp, #0x10 ; e1430091
   0x49CC1C: sub      x2, x29, #0xa8 ; a2a302d1
   0x49CC20: mov      x0, x20 ; e00314aa
   0x49CC24: ldr      x9, [x8, #0x38] ; 091d40f9
   0x49CC28: sub      x8, x29, #0x68 ; a8a301d1
   0x49CC2C: blr      x9 ; 20013fd6
   0x49CC30: sub      x8, x29, #0x18 ; a86300d1
   0x49CC34: sub      x0, x29, #0x68 ; a0a301d1
   0x49CC38: bl       #0x5e7ad4 ; a72b0594
   0x49CC3C: sub      x0, x29, #0xa8 ; a0a302d1
   0x49CC40: bl       #0xfb600 ; 707af197
   0x49CC44: add      x0, sp, #0x10 ; e0430091
   0x49CC48: bl       #0xfb600 ; 6e7af197
   0x49CC4C: ldur     x0, [x29, #-0x20] ; a0035ef8
   0x49CC50: cbz      x0, #0x49cc60 ; 800000b4
   0x49CC54: ldr      x8, [x0] ; 080040f9
   0x49CC58: ldr      x8, [x8, #0x18] ; 080d40f9
   0x49CC5C: blr      x8 ; 00013fd6
   0x49CC60: ldur     x0, [x29, #-0x18] ; a0835ef8
   0x49CC64: cbz      x0, #0x49cddc ; c00b00b4
   0x49CC68: adrp     x8, #0x3ec2000 ; 28d101d0
   0x49CC6C: sub      x1, x29, #0x20 ; a18300d1
   0x49CC70: ldr      x8, [x8, #0x818] ; 080d44f9
   0x49CC74: add      x3, sp, #0x10 ; e3430091
   0x49CC78: mov      w2, wzr ; e2031f2a
   0x49CC7C: strb     wzr, [sp, #0x10] ; ff430039
   0x49CC80: strb     wzr, [sp, #0x14] ; ff530039
   0x49CC84: strb     wzr, [sp, #0x18] ; ff630039
   0x49CC88: add      x8, x8, #0x10 ; 08410091
   0x49CC8C: strb     wzr, [sp, #0x1c] ; ff730039
   0x49CC90: strb     wzr, [sp, #0x20] ; ff830039
   0x49CC94: strb     wzr, [sp, #0x22] ; ff8b0039
   0x49CC98: strb     wzr, [sp, #0x24] ; ff930039
   0x49CC9C: stur     x8, [x29, #-0x20] ; a8031ef8
   0x49CCA0: sub      x8, x29, #0x28 ; a8a300d1
>> 0x49CCA4: bl       #0x656060 ; efe40694
   0x49CCA8: add      x20, x19, #0x18 ; 74620091
   0x49CCAC: mov      x0, x20 ; e00314aa
   0x49CCB0: bl       #0x82d198 ; 3a410e94
   0x49CCB4: tbz      w0, #0, #0x49ce00 ; 600a0036
   0x49CCB8: sub      x8, x29, #0x30 ; a8c300d1
   0x49CCBC: bl       #0x6fdda0 ; 39840994
   0x49CCC0: ldur     x0, [x29, #-0x30] ; a0035df8
   0x49CCC4: cbz      x0, #0x49cd84 ; 000600b4
   0x49CCC8: add      x8, sp, #0x10 ; e8430091
   0x49CCCC: bl       #0x9742e8 ; 875d1394
   0x49CCD0: sub      x8, x29, #0x38 ; a8e300d1
   0x49CCD4: add      x0, sp, #0x10 ; e0430091
   0x49CCD8: bl       #0x6c6310 ; 8ea50894
   0x49CCDC: ldur     x8, [x29, #-0x38] ; a8835cf8
   0x49CCE0: cbz      x8, #0x49cd84 ; 280500b4
   0x49CCE4: ldur     x0, [x29, #-0x30] ; a0035df8
   0x49CCE8: bl       #0x8dbd60 ; 1efc1094
   0x49CCEC: ldr      x20, [x0] ; 140040f9
   0x49CCF0: cbz      x20, #0x49ced0 ; 140f00b4
   0x49CCF4: mov      x19, x0 ; f30300aa
   0x49CCF8: ldur     x0, [x29, #-0x38] ; a0835cf8
   0x49CCFC: ldr      x8, [x0] ; 080040f9
   0x49CD00: ldr      x8, [x8, #0x68] ; 083540f9
   0x49CD04: blr      x8 ; 00013fd6
   0x49CD08: ldr      q0, [x0, #0x30] ; 000cc03d
   0x49CD0C: sub      x8, x29, #0x68 ; a8a301d1
   0x49CD10: mov      x0, x20 ; e00314aa
   0x49CD14: mov      v0.s[3], wzr ; e01f1c4e
   0x49CD18: bl       #0x8242c4 ; 6b1d0e94
   0x49CD1C: ldr      x0, [x19] ; 600240f9
   0x49CD20: sub      x8, x29, #0xa8 ; a8a302d1
   0x49CD24: sub      x1, x29, #0x68 ; a1a301d1
~~~

## Static PC 0x5E6DC0 (word 0x9401BCA8)

- ELF file offset: 0x5E7808; opcode: BL; mask: to native_pid_state_builder (0x656060)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x5E6BC0: ldr      x0, [x23, #0x38] ; e01e40f9
   0x5E6BC4: str      xzr, [x23, #0x38] ; ff1e00f9
   0x5E6BC8: cbnz     x0, #0x5e6f40 ; c01b00b5
   0x5E6BCC: ldr      x8, [x23] ; e80240f9
   0x5E6BD0: mov      x0, x23 ; e00317aa
   0x5E6BD4: ldr      x8, [x8, #0x50] ; 082940f9
   0x5E6BD8: blr      x8 ; 00013fd6
   0x5E6BDC: b        #0x5e6184 ; 6afdff17
   0x5E6BE0: ldr      x28, [sp] ; fc0340f9
   0x5E6BE4: mov      x9, xzr ; e9031faa
   0x5E6BE8: mov      x8, #0xd424 ; 88849ad2
   0x5E6BEC: movk     x8, #0x4ad4, lsl #16 ; 885aa9f2
   0x5E6BF0: ldr      x25, [x20, #0x1f8] ; 99fe40f9
   0x5E6BF4: movk     x8, #0x99bb, lsl #32 ; 6837d3f2
   0x5E6BF8: movk     x8, #0xac5, lsl #48 ; a858e1f2
   0x5E6BFC: str      xzr, [sp, #0x2028] ; ff1710f9
   0x5E6C00: str      x8, [sp, #0x2010] ; e80b10f9
   0x5E6C04: mov      w8, #0xf ; e8018052
   0x5E6C08: adrp     x10, #0x329e000 ; ca650190
   0x5E6C0C: add      x10, x10, #0x792 ; 4a491e91
   0x5E6C10: str      x8, [sp, #0x2020] ; e81310f9
   0x5E6C14: sub      x8, x29, #0x30 ; a8c300d1
   0x5E6C18: mov      x0, x24 ; e00318aa
   0x5E6C1C: str      x10, [sp, #0x2018] ; ea0f10f9
   0x5E6C20: add      x26, x9, x26 ; 3a011a8b
   0x5E6C24: bl       #0x38b90 ; db47e997
   0x5E6C28: add      x1, sp, #1, lsl #12 ; e1074091
   0x5E6C2C: add      x3, sp, #2, lsl #12 ; e30b4091
   0x5E6C30: sub      x4, x29, #0x30 ; a4c300d1
   0x5E6C34: add      x1, x1, #0xfc8 ; 21203f91
   0x5E6C38: add      x3, x3, #0x10 ; 63400091
   0x5E6C3C: mov      x0, x25 ; e00319aa
   0x5E6C40: mov      x2, x26 ; e2031aaa
   0x5E6C44: bl       #0x5e9bb0 ; db0b0094
   0x5E6C48: ldur     x0, [x29, #-0x18] ; a0835ef8
   0x5E6C4C: cbnz     x0, #0x5e6fdc ; 801c00b5
   0x5E6C50: ldr      x0, [sp, #0x2028] ; e01750f9
   0x5E6C54: cbz      x0, #0x5e6134 ; 00a7ffb4
   0x5E6C58: ldr      w8, [x0, #8] ; 080840b9
   0x5E6C5C: tst      w8, #3 ; 1f050072
   0x5E6C60: b.eq     #0x5e6134 ; a0a6ff54
   0x5E6C64: ldr      w8, [x0, #8] ; 080840b9
   0x5E6C68: add      x11, x0, #8 ; 0b200091
   0x5E6C6C: ldr      w9, [x0, #0xc] ; 090c40b9
   0x5E6C70: ldrb     w10, [x0, #0x10] ; 0a404039
   0x5E6C74: ldr      x2, [x0] ; 020040f9
   0x5E6C78: ldxr     w12, [x11] ; 6c7d5f88
   0x5E6C7C: sub      w13, w12, #0x400 ; 8d011051
   0x5E6C80: stlxr    w14, w13, [x11] ; 6dfd0e88
   0x5E6C84: cbnz     w14, #0x5e6c78 ; aeffff35
   0x5E6C88: and      w11, w12, #0xfffffc00 ; 8b551612
   0x5E6C8C: cmp      w11, #0x400 ; 7f011071
   0x5E6C90: b.ne     #0x5e6134 ; 21a5ff54
   0x5E6C94: and      x8, x8, #0x3fc ; 081d7e92
   0x5E6C98: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x5E6C9C: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x5E6CA0: lsr      x1, x8, #2 ; 01fd42d3
   0x5E6CA4: bl       #0x95a40 ; 67bbea97
   0x5E6CA8: b        #0x5e6134 ; 23fdff17
   0x5E6CAC: sub      x8, x29, #0x30 ; a8c300d1
   0x5E6CB0: mov      x0, x20 ; e00314aa
   0x5E6CB4: bl       #0x655364 ; acb90194
   0x5E6CB8: ldur     x0, [x29, #-0x30] ; a0035df8
   0x5E6CBC: cbz      x0, #0x5e61f8 ; e0a9ffb4
   0x5E6CC0: add      x8, sp, #2, lsl #12 ; e80b4091
   0x5E6CC4: mov      x1, x21 ; e10315aa
   0x5E6CC8: add      x8, x8, #0x10 ; 08410091
   0x5E6CCC: bl       #0x5e7db4 ; 3a040094
   0x5E6CD0: add      x0, sp, #2, lsl #12 ; e00b4091
   0x5E6CD4: sub      x8, x29, #0x58 ; a86301d1
   0x5E6CD8: add      x0, x0, #0x10 ; 00400091
   0x5E6CDC: bl       #0x5e7ad4 ; 7e030094
   0x5E6CE0: ldur     x19, [x29, #-0x58] ; b3835af8
   0x5E6CE4: cbz      x19, #0x5e7634 ; 934a00b4
   0x5E6CE8: adrp     x8, #0x3ec3000 ; e8c601b0
   0x5E6CEC: ldr      x8, [x8, #0x2b0] ; 085941f9
   0x5E6CF0: ldr      w8, [x8, #0x140] ; 084141b9
   0x5E6CF4: dmb      ishld ; bf3903d5
   0x5E6CF8: cbz      w8, #0x5e7640 ; 484a0034
   0x5E6CFC: adrp     x0, #0x3ec3000 ; e0c601b0
   0x5E6D00: mov      w1, #0x278 ; 014f8052
   0x5E6D04: ldr      x0, [x0, #0x2b0] ; 005841f9
   0x5E6D08: bl       #0x2bc834 ; cb56f397
   0x5E6D0C: cmp      w0, #0 ; 1f000071
   0x5E6D10: mov      w8, #3 ; 68008052
   0x5E6D14: csel     w22, wzr, w8, eq ; f603881a
   0x5E6D18: ldur     x8, [x29, #-0x58] ; a8835af8
   0x5E6D1C: ldrh     w24, [x8, #0x48] ; 18914079
   0x5E6D20: ldrh     w25, [x8, #0x64] ; 19c94079
   0x5E6D24: bl       #0x5e99d0 ; 2b0b0094
   0x5E6D28: tbnz     w0, #0, #0x5e7538 ; 80400037
   0x5E6D2C: strb     wzr, [x27, #0x48] ; 7f230139
   0x5E6D30: strb     wzr, [x27, #0x4c] ; 7f330139
   0x5E6D34: strb     wzr, [x27, #0x50] ; 7f430139
   0x5E6D38: strb     wzr, [x27, #0x54] ; 7f530139
   0x5E6D3C: strb     wzr, [x27, #0x58] ; 7f630139
   0x5E6D40: strb     wzr, [x27, #0x5a] ; 7f6b0139
   0x5E6D44: strb     wzr, [x27, #0x5c] ; 7f730139
   0x5E6D48: bl       #0x5e9904 ; ef0a0094
   0x5E6D4C: tst      x1, #0xff ; 3f1c40f2
   0x5E6D50: b.ne     #0x5e7648 ; c1470054
   0x5E6D54: bl       #0x5e99d0 ; 1f0b0094
   0x5E6D58: tbnz     w0, #0, #0x5e7554 ; e03f0037
   0x5E6D5C: adrp     x26, #0x3ec7000 ; 1ac701b0
   0x5E6D60: adrp     x25, #0x3ec2000 ; f9c60190
   0x5E6D64: ldr      x26, [x26, #0x1c8] ; 5ae740f9
   0x5E6D68: ldr      x9, [x26] ; 490340f9
   0x5E6D6C: ldr      x25, [x25, #0x1c8] ; 39e740f9
   0x5E6D70: cbz      x9, #0x5e6da8 ; c90100b4
   0x5E6D74: and      x8, x9, #0xfffff ; 284d4092
   0x5E6D78: add      x10, x25, x8, lsl #5 ; 2a17088b
   0x5E6D7C: add      x1, x10, #0x10 ; 41410091
   0x5E6D80: add      x8, x10, #0x28 ; 48a10091
   0x5E6D84: ldaxrh   w11, [x8] ; 0bfd5f48
   0x5E6D88: add      w12, w11, #1 ; 6c050011
   0x5E6D8C: stlxrh   w13, w12, [x8] ; 0cfd0d48
   0x5E6D90: cbnz     w13, #0x5e6d84 ; adffff35
   0x5E6D94: cbnz     w11, #0x5e76e8 ; ab4a0035
   0x5E6D98: ldaxrh   w9, [x8] ; 09fd5f48
   0x5E6D9C: sub      w9, w9, #1 ; 29050051
   0x5E6DA0: stlxrh   w10, w9, [x8] ; 09fd0a48
   0x5E6DA4: cbnz     w10, #0x5e6d98 ; aaffff35
   0x5E6DA8: ldur     x0, [x29, #-0x58] ; a0835af8
   0x5E6DAC: add      x3, sp, #2, lsl #12 ; e30b4091
   0x5E6DB0: add      x1, x20, #0x40 ; 81020191
   0x5E6DB4: sub      x8, x29, #0x38 ; a8e300d1
   0x5E6DB8: add      x3, x3, #0x10 ; 63400091
   0x5E6DBC: mov      w2, w22 ; e203162a
>> 0x5E6DC0: bl       #0x656060 ; a8bc0194
   0x5E6DC4: ldur     x0, [x29, #-0x38] ; a0835cf8
   0x5E6DC8: ldr      x8, [x0] ; 080040f9
   0x5E6DCC: ldr      x8, [x8, #0x8b8] ; 085d44f9
   0x5E6DD0: blr      x8 ; 00013fd6
   0x5E6DD4: tbnz     w0, #0, #0x5e7238 ; 20230037
   0x5E6DD8: ldur     x8, [x29, #-0x58] ; a8835af8
   0x5E6DDC: ldr      w2, [x8, #0x94] ; 029540b9
   0x5E6DE0: cmp      w2, #1 ; 5f040071
   0x5E6DE4: b.ge     #0x5e74e8 ; 2a380054
   0x5E6DE8: ldr      w9, [x8, #0x98] ; 099940b9
   0x5E6DEC: cmp      w9, #1 ; 3f050071
   0x5E6DF0: b.ge     #0x5e74fc ; 6a380054
   0x5E6DF4: ldr      w9, [x8, #0x9c] ; 099d40b9
   0x5E6DF8: cmp      w9, #1 ; 3f050071
   0x5E6DFC: b.ge     #0x5e7508 ; 6a380054
   0x5E6E00: ldr      w9, [x8, #0xa0] ; 09a140b9
   0x5E6E04: cmp      w9, #1 ; 3f050071
   0x5E6E08: b.ge     #0x5e7514 ; 6a380054
   0x5E6E0C: ldr      w9, [x8, #0xa4] ; 09a540b9
   0x5E6E10: cmp      w9, #1 ; 3f050071
   0x5E6E14: b.ge     #0x5e7520 ; 6a380054
   0x5E6E18: ldr      w8, [x8, #0xa8] ; 08a940b9
   0x5E6E1C: cmp      w8, #1 ; 1f050071
   0x5E6E20: b.ge     #0x5e752c ; 6a380054
   0x5E6E24: ldr      x9, [x26] ; 490340f9
   0x5E6E28: cbz      x9, #0x5e6e60 ; c90100b4
   0x5E6E2C: and      x8, x9, #0xfffff ; 284d4092
   0x5E6E30: add      x10, x25, x8, lsl #5 ; 2a17088b
   0x5E6E34: add      x1, x10, #0x10 ; 41410091
   0x5E6E38: add      x8, x10, #0x28 ; 48a10091
   0x5E6E3C: ldaxrh   w11, [x8] ; 0bfd5f48
   0x5E6E40: add      w12, w11, #1 ; 6c050011
~~~

## Static PC 0x653F24 (word 0x9400084F)

- ELF file offset: 0x65496C; opcode: BL; mask: to native_pid_state_builder (0x656060)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x653D24: ldrb     w10, [x24, #0x10] ; 0a434039
   0x653D28: ldr      x2, [x24] ; 020340f9
   0x653D2C: ldxr     w11, [x19] ; 6b7e5f88
   0x653D30: sub      w12, w11, #0x400 ; 6c011051
   0x653D34: stlxr    w13, w12, [x19] ; 6cfe0d88
   0x653D38: cbnz     w13, #0x653d2c ; adffff35
   0x653D3C: and      w11, w11, #0xfffffc00 ; 6b551612
   0x653D40: cmp      w11, #0x400 ; 7f011071
   0x653D44: b.ne     #0x653d98 ; a1020054
   0x653D48: and      x8, x8, #0x3fc ; 081d7e92
   0x653D4C: mov      x0, x24 ; e00318aa
   0x653D50: orr      x8, x8, x9, lsl #10 ; 082909aa
   0x653D54: orr      x8, x8, x10, lsl #42 ; 08a90aaa
   0x653D58: lsr      x1, x8, #2 ; 01fd42d3
   0x653D5C: bl       #0x95a40 ; 3907e997
   0x653D60: b        #0x653d98 ; 0e000014
   0x653D64: add      x1, sp, #0x98 ; e1630291
   0x653D68: mov      x0, x23 ; e00317aa
   0x653D6C: bl       #0x60e3f8 ; a3e9fe97
   0x653D70: ldr      x19, [sp, #0x238] ; f31f41f9
   0x653D74: b        #0x653bc8 ; 95ffff17
   0x653D78: add      x1, sp, #0x98 ; e1630291
   0x653D7C: mov      x0, x23 ; e00317aa
   0x653D80: bl       #0x60e3f8 ; 9ee9fe97
   0x653D84: ldr      x8, [sp, #0x238] ; e81f41f9
   0x653D88: b        #0x653c3c ; adffff17
   0x653D8C: sub      x8, x29, #0x50 ; a84301d1
   0x653D90: mov      x0, x21 ; e00315aa
   0x653D94: bl       #0x283f0 ; 9751e797
   0x653D98: ldur     x8, [x29, #-0x50] ; a8035bf8
   0x653D9C: str      x8, [sp, #0xa8] ; e85700f9
   0x653DA0: ldr      x8, [x21, #0xd8] ; a86e40f9
   0x653DA4: ldrb     w8, [x8] ; 08014039
   0x653DA8: cbnz     w8, #0x653e88 ; 08070035
   0x653DAC: ldur     x0, [x29, #-0x58] ; a0835af8
   0x653DB0: add      x1, x21, #0x20 ; a1820091
   0x653DB4: add      x8, sp, #0x98 ; e8630291
   0x653DB8: bl       #0x2664a0 ; ba49f097
   0x653DBC: ldr      x9, [sp, #0x98] ; e94f40f9
   0x653DC0: cbz      x9, #0x653e00 ; 090200b4
   0x653DC4: adrp     x19, #0x3ec2000 ; 73c301f0
   0x653DC8: and      x8, x9, #0xfffff ; 284d4092
   0x653DCC: ldr      x19, [x19, #0x1c8] ; 73e640f9
   0x653DD0: add      x10, x19, x8, lsl #5 ; 6a16088b
   0x653DD4: add      x1, x10, #0x10 ; 41410091
   0x653DD8: add      x8, x10, #0x28 ; 48a10091
   0x653DDC: ldaxrh   w11, [x8] ; 0bfd5f48
   0x653DE0: add      w12, w11, #1 ; 6c050011
   0x653DE4: stlxrh   w13, w12, [x8] ; 0cfd0d48
   0x653DE8: cbnz     w13, #0x653ddc ; adffff35
   0x653DEC: cbnz     w11, #0x654a04 ; cb600035
   0x653DF0: ldaxrh   w9, [x8] ; 09fd5f48
   0x653DF4: sub      w9, w9, #1 ; 29050051
   0x653DF8: stlxrh   w10, w9, [x8] ; 09fd0a48
   0x653DFC: cbnz     w10, #0x653df0 ; aaffff35
   0x653E00: ldr      x0, [sp, #0xa8] ; e05740f9
   0x653E04: cbnz     x0, #0x6541dc ; c01e00b5
   0x653E08: add      x0, sp, #0xd0 ; e0430391
   0x653E0C: bl       #0x3f1c68 ; 9777f697
   0x653E10: ldur     x19, [x29, #-0x58] ; b3835af8
   0x653E14: cbz      x19, #0x653e3c ; 530100b4
   0x653E18: ldr      x8, [x19, #0x38] ; 681e40f9
   0x653E1C: add      x10, x8, #0x1a ; 0a690091
   0x653E20: ldaxrh   w9, [x10] ; 49fd5f48
   0x653E24: sub      w11, w9, #1 ; 2b050051
   0x653E28: stlxrh   w12, w11, [x10] ; 4bfd0c48
   0x653E2C: cbnz     w12, #0x653e20 ; acffff35
   0x653E30: cmp      w9, #1 ; 3f050071
   0x653E34: b.eq     #0x654758 ; 20490054
   0x653E38: cbz      w9, #0x6550d0 ; c9940034
   0x653E3C: add      sp, sp, #2, lsl #12 ; ff0b4091
   0x653E40: add      sp, sp, #0xd0 ; ff430391
   0x653E44: ldp      x20, x19, [sp, #0x50] ; f44f45a9
   0x653E48: ldp      x22, x21, [sp, #0x40] ; f65744a9
   0x653E4C: ldp      x24, x23, [sp, #0x30] ; f85f43a9
   0x653E50: ldp      x26, x25, [sp, #0x20] ; fa6742a9
   0x653E54: ldp      x28, x27, [sp, #0x10] ; fc6f41a9
   0x653E58: ldp      x29, x30, [sp], #0x60 ; fd7bc6a8
   0x653E5C: ret       ; c0035fd6
   0x653E60: sub      x0, x29, #0x50 ; a04301d1
   0x653E64: bl       #0x68450 ; 7b51e897
   0x653E68: ldur     q0, [x29, #-0x50] ; a003db3c
   0x653E6C: ldrb     w8, [sp, #0x110] ; e8434439
   0x653E70: str      q0, [sp, #0xe0] ; e03b803d
   0x653E74: cbnz     w8, #0x653e80 ; 68000035
   0x653E78: mov      w8, #1 ; 28008052
   0x653E7C: strb     w8, [sp, #0x110] ; e8430439
   0x653E80: ldr      q0, [sp, #0x70] ; e01fc03d
   0x653E84: b        #0x653b18 ; 25ffff17
   0x653E88: ldr      x9, [x20, #0x1b0] ; 89da40f9
   0x653E8C: cbz      x9, #0x653ecc ; 090200b4
   0x653E90: adrp     x10, #0x3ec2000 ; 6ac301f0
   0x653E94: and      x8, x9, #0xfffff ; 284d4092
   0x653E98: ldr      x10, [x10, #0x1c8] ; 4ae540f9
   0x653E9C: add      x10, x10, x8, lsl #5 ; 4a15088b
   0x653EA0: add      x1, x10, #0x10 ; 41410091
   0x653EA4: add      x8, x10, #0x28 ; 48a10091
   0x653EA8: ldaxrh   w11, [x8] ; 0bfd5f48
   0x653EAC: add      w12, w11, #1 ; 6c050011
   0x653EB0: stlxrh   w13, w12, [x8] ; 0cfd0d48
   0x653EB4: cbnz     w13, #0x653ea8 ; adffff35
   0x653EB8: cbnz     w11, #0x654c98 ; 0b6f0035
   0x653EBC: ldaxrh   w9, [x8] ; 09fd5f48
   0x653EC0: sub      w9, w9, #1 ; 29050051
   0x653EC4: stlxrh   w10, w9, [x8] ; 09fd0a48
   0x653EC8: cbnz     w10, #0x653ebc ; aaffff35
   0x653ECC: mov      x26, x22 ; fa0316aa
   0x653ED0: ldur     x0, [x29, #-0x58] ; a0835af8
   0x653ED4: add      x1, x21, #0xd0 ; a1420391
   0x653ED8: sub      x8, x29, #0x50 ; a84301d1
   0x653EDC: bl       #0x655e74 ; e6070094
   0x653EE0: add      x8, sp, #0x98 ; e8630291
   0x653EE4: sub      x0, x29, #0x50 ; a04301d1
   0x653EE8: bl       #0x5e7ad4 ; fb4efe97
   0x653EEC: ldr      x0, [sp, #0x98] ; e04f40f9
   0x653EF0: cbz      x0, #0x653e00 ; 80f8ffb4
   0x653EF4: sub      x8, x29, #0x50 ; a84301d1
   0x653EF8: add      x1, x20, #0x40 ; 81020191
   0x653EFC: strb     wzr, [x8] ; 1f010039
   0x653F00: strb     wzr, [x8, #4] ; 1f110039
   0x653F04: sub      x3, x29, #0x50 ; a34301d1
   0x653F08: mov      w2, wzr ; e2031f2a
   0x653F0C: strb     wzr, [x8, #8] ; 1f210039
   0x653F10: strb     wzr, [x8, #0xc] ; 1f310039
   0x653F14: strb     wzr, [x8, #0x10] ; 1f410039
   0x653F18: strb     wzr, [x8, #0x12] ; 1f490039
   0x653F1C: strb     wzr, [x8, #0x14] ; 1f510039
   0x653F20: sub      x8, x29, #0x18 ; a86300d1
>> 0x653F24: bl       #0x656060 ; 4f080094
   0x653F28: ldr      x24, [sp, #0x98] ; f84f40f9
   0x653F2C: mov      w9, #0x2fffffff ; 0900ba12
   0x653F30: ldur     x0, [x29, #-0x18] ; a0835ef8
   0x653F34: ldr      w8, [x24, #0x68] ; 086b40b9
   0x653F38: cmp      w8, w9 ; 1f01096b
   0x653F3C: b.eq     #0x654970 ; a0510054
   0x653F40: ldr      x8, [x0] ; 080040f9
   0x653F44: ldr      x8, [x8, #0x6e0] ; 087143f9
   0x653F48: blr      x8 ; 00013fd6
   0x653F4C: ldr      x24, [sp, #0x98] ; f84f40f9
   0x653F50: ldur     x8, [x29, #-0x18] ; a8835ef8
   0x653F54: str      x8, [sp, #0x88] ; e84700f9
   0x653F58: cbnz     x24, #0x654974 ; f85000b5
   0x653F5C: ldr      x24, [sp, #0x88] ; f84740f9
   0x653F60: cbz      x24, #0x653e00 ; 18f5ffb4
   0x653F64: ldr      x19, [x24, #0x38] ; 131f40f9
   0x653F68: ldr      x8, [x19, #0x10] ; 680a40f9
   0x653F6C: cbz      x8, #0x6550d0 ; 288b00b4
   0x653F70: add      x9, x19, #0x1a ; 696a0091
   0x653F74: ldaxrh   w8, [x9] ; 28fd5f48
   0x653F78: add      w10, w8, #1 ; 0a050011
   0x653F7C: stlxrh   w11, w10, [x9] ; 2afd0b48
   0x653F80: cbnz     w11, #0x653f74 ; abffff35
   0x653F84: cbz      w8, #0x6547f4 ; 88430034
   0x653F88: mov      w9, #0xffff ; e9ff9f52
   0x653F8C: cmp      w8, w9 ; 1f01096b
   0x653F90: b.eq     #0x6550d0 ; 008a0054
   0x653F94: ldr      x19, [x24, #0x38] ; 131f40f9
   0x653F98: ldr      x8, [x19, #0x10] ; 680a40f9
   0x653F9C: cbz      x8, #0x6550d0 ; a88900b4
   0x653FA0: add      x9, x19, #0x1a ; 696a0091
   0x653FA4: ldaxrh   w8, [x9] ; 28fd5f48
~~~

## Static PC 0x9CE758 (word 0x97F21E42)

- ELF file offset: 0x9CF1A0; opcode: BL; mask: to native_pid_state_builder (0x656060)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x9CE558: str      x10, [sp, #0x30] ; ea1b00f9
   0x9CE55C: add      x10, sp, #0x1f0 ; eac30791
   0x9CE560: str      x9, [sp, #0x28] ; e91700f9
   0x9CE564: add      x9, x10, #0x150 ; 49410591
   0x9CE568: madd     x8, x8, x11, x12 ; 08310b9b
   0x9CE56C: str      x9, [sp, #0x20] ; e91300f9
   0x9CE570: add      x9, x10, #0x148 ; 49210591
   0x9CE574: str      x12, [sp, #0x50] ; ec2b00f9
   0x9CE578: str      x8, [sp, #0x38] ; e81f00f9
   0x9CE57C: add      x8, x10, #0x160 ; 48810591
   0x9CE580: stp      x8, x9, [sp, #0x10] ; e82701a9
   0x9CE584: ldr      x8, [sp, #0x50] ; e82b40f9
   0x9CE588: add      x0, x8, #0x40 ; 00010191
   0x9CE58C: ldur     x23, [x29, #-0x48] ; b7835bf8
   0x9CE590: add      x8, sp, #2, lsl #12 ; e80b4091
   0x9CE594: add      x8, x8, #0x1a0 ; 08810691
   0x9CE598: bl       #0x38b90 ; 7ea9d997
   0x9CE59C: add      x1, sp, #2, lsl #12 ; e10b4091
   0x9CE5A0: add      x8, sp, #0xb0 ; e8c30291
   0x9CE5A4: mov      x0, x23 ; e00317aa
   0x9CE5A8: add      x1, x1, #0x1a0 ; 21800691
   0x9CE5AC: bl       #0x91e934 ; e240fd97
   0x9CE5B0: ldr      x9, [sp, #0xb0] ; e95b40f9
   0x9CE5B4: cbz      x9, #0x9ce5ec ; c90100b4
   0x9CE5B8: and      x8, x9, #0xfffff ; 284d4092
   0x9CE5BC: add      x10, x26, x8, lsl #5 ; 4a17088b
   0x9CE5C0: add      x1, x10, #0x10 ; 41410091
   0x9CE5C4: add      x8, x10, #0x28 ; 48a10091
   0x9CE5C8: ldaxrh   w11, [x8] ; 0bfd5f48
   0x9CE5CC: add      w12, w11, #1 ; 6c050011
   0x9CE5D0: stlxrh   w13, w12, [x8] ; 0cfd0d48
   0x9CE5D4: cbnz     w13, #0x9ce5c8 ; adffff35
   0x9CE5D8: cbnz     w11, #0x9cf4f4 ; eb780035
   0x9CE5DC: ldaxrh   w9, [x8] ; 09fd5f48
   0x9CE5E0: sub      w9, w9, #1 ; 29050051
   0x9CE5E4: stlxrh   w10, w9, [x8] ; 09fd0a48
   0x9CE5E8: cbnz     w10, #0x9ce5dc ; aaffff35
   0x9CE5EC: str      xzr, [sp, #0x60] ; ff3300f9
   0x9CE5F0: ldr      x0, [sp, #0x21b8] ; e0df50f9
   0x9CE5F4: cbnz     x0, #0x9cedb8 ; 203e00b5
   0x9CE5F8: ldr      x8, [sp, #0x60] ; e83340f9
   0x9CE5FC: cbz      x8, #0x9ced20 ; 283900b4
   0x9CE600: ldr      x9, [sp, #0x60] ; e93340f9
   0x9CE604: ldp      x9, x8, [x9, #0x40] ; 292144a9
   0x9CE608: subs     x19, x8, x9 ; 130109eb
   0x9CE60C: b.eq     #0x9cecf8 ; 60370054
   0x9CE610: ldr      x20, [sp, #0x58] ; f42f40f9
   0x9CE614: mov      x0, x20 ; e00314aa
   0x9CE618: ldr      x8, [x20] ; 880240f9
   0x9CE61C: ldr      x8, [x8, #0x18] ; 080d40f9
   0x9CE620: blr      x8 ; 00013fd6
   0x9CE624: ldr      x8, [x20] ; 880240f9
   0x9CE628: mov      x0, x20 ; e00314aa
   0x9CE62C: ldr      x8, [x8, #0x10] ; 080940f9
   0x9CE630: blr      x8 ; 00013fd6
   0x9CE634: cmp      x19, #8 ; 7f2200f1
   0x9CE638: b.eq     #0x9ced64 ; 60390054
   0x9CE63C: asr      x8, x19, #3 ; 68fe4393
   0x9CE640: clz      x9, x8 ; 0911c0da
   0x9CE644: lsl      x10, x8, x9 ; 0a21c99a
   0x9CE648: tst      x10, #0x7fffffffffffffff ; 5ff940f2
   0x9CE64C: mov      w10, #0x3f ; ea078052
   0x9CE650: cinc     x10, x10, ne ; 4a058a9a
   0x9CE654: sub      x9, x10, x9 ; 490109cb
   0x9CE658: lsr      x10, x9, #6 ; 2afd46d3
   0x9CE65C: tst      x9, #0x3f ; 3f1540f2
   0x9CE660: and      w11, w9, #0xff ; 2b1d0012
   0x9CE664: cinc     x10, x10, ne ; 4a058a9a
   0x9CE668: and      w12, w10, #0xff ; 4c1d0012
   0x9CE66C: cmp      x10, x9 ; 5f0109eb
   0x9CE670: udiv     w11, w11, w12 ; 6b09cc1a
   0x9CE674: mov      x12, #-1 ; 0c008092
   0x9CE678: neg      x11, x11 ; eb030bcb
   0x9CE67C: lsr      x11, x12, x11 ; 8b25cb9a
   0x9CE680: csel     x9, xzr, x11, hi ; e9838b9a
   0x9CE684: ldp      x10, x11, [x0] ; 0a2c40a9
   0x9CE688: add      x12, x10, x11 ; 4c010b8b
   0x9CE68C: eor      x13, x10, x11 ; 4d010bca
   0x9CE690: and      x12, x12, x9 ; 8c01098a
   0x9CE694: ror      x10, x10, #0x28 ; 4aa1ca93
   0x9CE698: eor      x10, x10, x13, lsl #16 ; 4a410dca
   0x9CE69C: ror      x11, x13, #0x1b ; ab6dcd93
   0x9CE6A0: cmp      x12, x8 ; 9f0108eb
   0x9CE6A4: eor      x10, x10, x13 ; 4a010dca
   0x9CE6A8: b.hs     #0x9ce688 ; 02ffff54
   0x9CE6AC: stp      x10, x11, [x0] ; 0a2c00a9
   0x9CE6B0: ldr      x8, [sp, #0x60] ; e83340f9
   0x9CE6B4: ldr      x8, [x8, #0x40] ; 082140f9
   0x9CE6B8: ldr      x8, [x8, x12, lsl #3] ; 08796cf8
   0x9CE6BC: str      x8, [sp, #0x2198] ; e8cf10f9
   0x9CE6C0: cbz      x8, #0x9ce6e4 ; 280100b4
   0x9CE6C4: ldr      w9, [x8, #8] ; 090940b9
   0x9CE6C8: tst      w9, #3 ; 3f050072
   0x9CE6CC: b.eq     #0x9ce6e4 ; c0000054
   0x9CE6D0: add      x8, x8, #8 ; 08210091
   0x9CE6D4: ldxr     w9, [x8] ; 097d5f88
   0x9CE6D8: add      w9, w9, #0x400 ; 29011011
   0x9CE6DC: stxr     w10, w9, [x8] ; 097d0a88
   0x9CE6E0: cbnz     w10, #0x9ce6d4 ; aaffff35
   0x9CE6E4: ldur     x24, [x29, #-0x48] ; b8835bf8
   0x9CE6E8: add      x0, sp, #2, lsl #12 ; e00b4091
   0x9CE6EC: add      x8, sp, #0x1f0 ; e8c30791
   0x9CE6F0: add      x0, x0, #0x198 ; 00600691
   0x9CE6F4: bl       #0x38b90 ; 27a9d997
   0x9CE6F8: add      x8, sp, #0xb0 ; e8c30291
   0x9CE6FC: add      x1, sp, #0x1f0 ; e1c30791
   0x9CE700: mov      x0, x24 ; e00318aa
   0x9CE704: bl       #0x655e74 ; dc1df297
   0x9CE708: add      x8, sp, #2, lsl #12 ; e80b4091
   0x9CE70C: add      x0, sp, #0xb0 ; e0c30291
   0x9CE710: add      x8, x8, #0x190 ; 08410691
   0x9CE714: bl       #0x5e7ad4 ; f064f097
   0x9CE718: ldr      x0, [sp, #0x208] ; e00741f9
   0x9CE71C: cbnz     x0, #0x9cedf8 ; e03600b5
   0x9CE720: ldr      x0, [sp, #0x2190] ; e0cb50f9
   0x9CE724: cbz      x0, #0x9cecf0 ; 602e00b4
   0x9CE728: ldr      x1, [sp, #0x58] ; e12f40f9
   0x9CE72C: add      x8, sp, #2, lsl #12 ; e80b4091
   0x9CE730: add      x3, sp, #0x1f0 ; e3c30791
   0x9CE734: add      x8, x8, #0x188 ; 08210691
   0x9CE738: mov      w2, wzr ; e2031f2a
   0x9CE73C: strb     wzr, [sp, #0x1f0] ; ffc30739
   0x9CE740: strb     wzr, [sp, #0x1f4] ; ffd30739
   0x9CE744: strb     wzr, [sp, #0x1f8] ; ffe30739
   0x9CE748: strb     wzr, [sp, #0x1fc] ; fff30739
   0x9CE74C: strb     wzr, [sp, #0x200] ; ff030839
   0x9CE750: strb     wzr, [sp, #0x202] ; ff0b0839
   0x9CE754: strb     wzr, [sp, #0x204] ; ff130839
>> 0x9CE758: bl       #0x656060 ; 421ef297
   0x9CE75C: ldr      x0, [sp, #0x2188] ; e0c750f9
   0x9CE760: cbz      x0, #0x9cece8 ; 402c00b4
   0x9CE764: ldr      x8, [x0] ; 080040f9
   0x9CE768: ldr      x8, [x8, #0x1b0] ; 08d940f9
   0x9CE76C: blr      x8 ; 00013fd6
   0x9CE770: str      w0, [sp, #0x4c] ; e04f00b9
   0x9CE774: ldr      x0, [sp, #0x2188] ; e0c750f9
   0x9CE778: ldr      x8, [x0] ; 080040f9
   0x9CE77C: ldr      x8, [x8, #0x1b8] ; 08dd40f9
   0x9CE780: blr      x8 ; 00013fd6
   0x9CE784: str      w0, [sp, #0x48] ; e04b00b9
   0x9CE788: ldr      x0, [sp, #0x2188] ; e0c750f9
   0x9CE78C: ldr      x8, [x0] ; 080040f9
   0x9CE790: ldr      x8, [x8, #0x140] ; 08a140f9
   0x9CE794: blr      x8 ; 00013fd6
   0x9CE798: str      w0, [sp, #0x44] ; e04700b9
   0x9CE79C: ldr      x0, [sp, #0x2188] ; e0c750f9
   0x9CE7A0: ldr      x8, [x0] ; 080040f9
   0x9CE7A4: ldr      x8, [x8, #0x6c0] ; 086143f9
   0x9CE7A8: blr      x8 ; 00013fd6
   0x9CE7AC: str      w0, [sp, #0x40] ; e04300b9
   0x9CE7B0: add      x0, sp, #0x1f0 ; e0c30791
   0x9CE7B4: bl       #0x3f1488 ; 358be897
   0x9CE7B8: ldr      x1, [sp, #0x70] ; e13b40f9
   0x9CE7BC: add      x0, sp, #0xb0 ; e0c30291
   0x9CE7C0: bl       #0x939f8 ; 8e14db97
   0x9CE7C4: ldr      x19, [sp, #0x50] ; f32b40f9
   0x9CE7C8: ldr      x0, [sp, #0x30] ; e01b40f9
   0x9CE7CC: ldr      x1, [x19, #0x88] ; 614640f9
   0x9CE7D0: bl       #0x541578 ; 6acbed97
   0x9CE7D4: ldr      x0, [sp, #0x28] ; e01740f9
   0x9CE7D8: add      x1, x19, #0x48 ; 61220191
~~~

## Static PC 0x294F57C (word 0x97741AB9)

- ELF file offset: 0x294FFC4; opcode: BL; mask: to native_pid_state_builder (0x656060)
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x294F37C: stp      x29, x30, [sp, #-0x50]! ; fd7bbba9
   0x294F380: stp      x28, x25, [sp, #0x10] ; fc6701a9
   0x294F384: mov      x29, sp ; fd030091
   0x294F388: stp      x24, x23, [sp, #0x20] ; f85f02a9
   0x294F38C: stp      x22, x21, [sp, #0x30] ; f65703a9
   0x294F390: stp      x20, x19, [sp, #0x40] ; f44f04a9
   0x294F394: sub      sp, sp, #0x350 ; ff430dd1
   0x294F398: stp      x2, x1, [x29, #-0x10] ; a2073fa9
   0x294F39C: stur     x3, [x29, #-0x18] ; a3831ef8
   0x294F3A0: cbz      x1, #0x294fb1c ; e13b00b4
   0x294F3A4: cbz      x2, #0x294fb1c ; c23b00b4
   0x294F3A8: mov      x19, x0 ; f30300aa
   0x294F3AC: sub      x8, x29, #0x38 ; a8e300d1
   0x294F3B0: sub      x0, x29, #8 ; a02300d1
   0x294F3B4: bl       #0x65fb40 ; e3417497
   0x294F3B8: sub      x8, x29, #0x58 ; a86301d1
   0x294F3BC: sub      x0, x29, #0x10 ; a04300d1
   0x294F3C0: bl       #0x65fb40 ; e0417497
   0x294F3C4: sub      x8, x29, #0x78 ; a8e301d1
   0x294F3C8: sub      x0, x29, #0x18 ; a06300d1
   0x294F3CC: bl       #0x65fb40 ; dd417497
   0x294F3D0: adrp     x22, #0x610b000 ; f6bd0190
   0x294F3D4: add      x22, x22, #0x200 ; d6020891
   0x294F3D8: ldr      w8, [x22, #0x400] ; c80244b9
   0x294F3DC: dmb      ishld ; bf3903d5
   0x294F3E0: cbz      w8, #0x294fb04 ; 28390034
   0x294F3E4: adrp     x1, #0x31f1000 ; 014500d0
   0x294F3E8: add      x1, x1, #0xe2d ; 21b43891
   0x294F3EC: add      x0, sp, #0x120 ; e0830491
   0x294F3F0: bl       #0x7defc0 ; f43e7a97
   0x294F3F4: sub      x8, x29, #0x98 ; a86302d1
   0x294F3F8: add      x0, sp, #0x120 ; e0830491
   0x294F3FC: bl       #0x38b90 ; e5a55b97
   0x294F400: add      x0, sp, #0x120 ; e0830491
   0x294F404: bl       #0x7def60 ; d73e7a97
   0x294F408: add      x8, sp, #0x120 ; e8830491
   0x294F40C: bl       #0x6fdda0 ; 65ba7697
   0x294F410: ldr      x0, [sp, #0x120] ; e09340f9
   0x294F414: add      x8, sp, #0x28 ; e8a30091
   0x294F418: bl       #0xb05b90 ; ded98697
   0x294F41C: add      x0, sp, #0x120 ; e0830491
   0x294F420: bl       #0x6a3f60 ; d0527597
   0x294F424: ldr      x0, [sp, #0x28] ; e01740f9
   0x294F428: cbz      x0, #0x294fb38 ; 803800b4
   0x294F42C: add      x8, sp, #0x120 ; e8830491
   0x294F430: sub      x1, x29, #0x58 ; a16301d1
   0x294F434: mov      w2, wzr ; e2031f2a
   0x294F438: bl       #0x265d10 ; 365a6497
   0x294F43C: add      x8, sp, #8 ; e8230091
   0x294F440: add      x0, sp, #0x120 ; e0830491
   0x294F444: bl       #0x60e8e0 ; 27fd7297
   0x294F448: ldr      x8, [sp, #8] ; e80740f9
   0x294F44C: cbz      x8, #0x294fb40 ; a83700b4
   0x294F450: add      x0, x8, #0x40 ; 00010191
   0x294F454: add      x8, sp, #0x120 ; e8830491
   0x294F458: bl       #0x38b90 ; cea55b97
   0x294F45C: sub      x0, x29, #0x98 ; a06302d1
   0x294F460: add      x1, sp, #0x120 ; e1830491
   0x294F464: bl       #0x5dda40 ; 77397297
   0x294F468: add      x0, sp, #0x120 ; e0830491
   0x294F46C: bl       #0xfb600 ; 65b05e97
   0x294F470: ldr      x8, [sp, #8] ; e80740f9
   0x294F474: ldrb     w23, [x8, #0x4a] ; 17294139
   0x294F478: add      x0, sp, #8 ; e0230091
   0x294F47C: bl       #0x60e830 ; edfc7297
   0x294F480: add      x0, sp, #0x28 ; e0a30091
   0x294F484: bl       #0x60e780 ; bffc7297
   0x294F488: ldr      x0, [x22, #8] ; c00640f9
   0x294F48C: adrp     x1, #0x3393000 ; 21520090
   0x294F490: add      x1, x1, #0xfad ; 21b43e91
   0x294F494: sub      x8, x29, #0xa8 ; a8a302d1
   0x294F498: stur     xzr, [x29, #-0xa0] ; bf0316f8
   0x294F49C: bl       #0xc3ec90 ; fdbd8b97
   0x294F4A0: adrp     x0, #0x3eca000 ; c0ab00f0
   0x294F4A4: add      x8, sp, #0x120 ; e8830491
   0x294F4A8: ldr      x0, [x0, #0x658] ; 002c43f9
   0x294F4AC: bl       #0x511f90 ; b90a6f97
   0x294F4B0: ldr      x0, [sp, #0x120] ; e09340f9
   0x294F4B4: sub      x8, x29, #0xb8 ; a8e302d1
   0x294F4B8: bl       #0x514fe0 ; ca166f97
   0x294F4BC: add      x0, sp, #0x120 ; e0830491
   0x294F4C0: bl       #0x5120c0 ; 000b6f97
   0x294F4C4: sub      x0, x29, #0xb8 ; a0e302d1
   0x294F4C8: bl       #0xbf9740 ; 9ea88a97
   0x294F4CC: tbnz     w0, #0, #0x294faec ; 00310037
   0x294F4D0: sub      x8, x29, #0xc0 ; a80303d1
   0x294F4D4: sub      x0, x29, #0xb8 ; a0e302d1
   0x294F4D8: bl       #0x514e5c ; 61166f97
   0x294F4DC: adrp     x0, #0x3ec6000 ; a0ab00f0
   0x294F4E0: ldur     x20, [x29, #-0xc0] ; b40354f8
   0x294F4E4: add      x8, sp, #0x120 ; e8830491
   0x294F4E8: ldr      x0, [x0, #0xdc8] ; 00e446f9
   0x294F4EC: bl       #0x421c ; 4cd35a97
   0x294F4F0: ldr      x8, [x20] ; 880240f9
   0x294F4F4: add      x1, sp, #0x120 ; e1830491
   0x294F4F8: sub      x2, x29, #0x38 ; a2e300d1
   0x294F4FC: mov      x0, x20 ; e00314aa
   0x294F500: ldr      x9, [x8, #0x38] ; 091d40f9
   0x294F504: add      x8, sp, #8 ; e8230091
   0x294F508: blr      x9 ; 20013fd6
   0x294F50C: add      x8, sp, #0x28 ; e8a30091
   0x294F510: add      x0, sp, #8 ; e0230091
   0x294F514: bl       #0x5e7ad4 ; 70617297
   0x294F518: add      x0, sp, #0x120 ; e0830491
   0x294F51C: bl       #0xfb600 ; 39b05e97
   0x294F520: ldur     x0, [x29, #-0xc0] ; a00354f8
   0x294F524: cbz      x0, #0x294f534 ; 800000b4
   0x294F528: ldr      x8, [x0] ; 080040f9
   0x294F52C: ldr      x8, [x8, #0x18] ; 080d40f9
   0x294F530: blr      x8 ; 00013fd6
   0x294F534: ldr      x0, [sp, #0x28] ; e01740f9
   0x294F538: add      x20, sp, #0x28 ; f4a30091
   0x294F53C: cbz      x0, #0x294f61c ; 000700b4
   0x294F540: adrp     x8, #0x3ec2000 ; 88ab00f0
   0x294F544: add      x1, sp, #8 ; e1230091
   0x294F548: ldr      x8, [x8, #0x818] ; 080d44f9
   0x294F54C: add      x3, sp, #0x120 ; e3830491
   0x294F550: mov      w2, wzr ; e2031f2a
   0x294F554: strb     wzr, [sp, #0x120] ; ff830439
   0x294F558: strb     wzr, [sp, #0x124] ; ff930439
   0x294F55C: strb     wzr, [sp, #0x128] ; ffa30439
   0x294F560: add      x8, x8, #0x10 ; 08410091
   0x294F564: strb     wzr, [sp, #0x12c] ; ffb30439
   0x294F568: strb     wzr, [sp, #0x130] ; ffc30439
   0x294F56C: strb     wzr, [sp, #0x132] ; ffcb0439
   0x294F570: strb     wzr, [sp, #0x134] ; ffd30439
   0x294F574: str      x8, [sp, #8] ; e80700f9
   0x294F578: sub      x8, x29, #0xc0 ; a80303d1
>> 0x294F57C: bl       #0x656060 ; b91a7497
   0x294F580: sub      x0, x29, #0xa0 ; a08302d1
   0x294F584: mov      x1, xzr ; e1031faa
   0x294F588: bl       #0xd0156c ; f9c78e97
   0x294F58C: ldur     x8, [x29, #-0xc0] ; a80354f8
   0x294F590: sub      x0, x29, #0xc0 ; a00303d1
   0x294F594: stur     xzr, [x29, #-0xc0] ; bf0314f8
   0x294F598: stur     x8, [x29, #-0xa0] ; a80316f8
   0x294F59C: bl       #0xa0d050 ; adf68297
   0x294F5A0: adrp     x8, #0x612c000 ; e8be01b0
   0x294F5A4: add      x8, x8, #0x800 ; 08012091
   0x294F5A8: ldr      w8, [x8, #0x140] ; 084141b9
   0x294F5AC: dmb      ishld ; bf3903d5
   0x294F5B0: cbz      w8, #0x294f61c ; 68030034
   0x294F5B4: ldur     x8, [x29, #-0x70] ; a80359f8
   0x294F5B8: ldrb     w8, [x8] ; 08014039
   0x294F5BC: cbz      w8, #0x294f61c ; 08030034
   0x294F5C0: mov      x9, #0x5852 ; 490a8bd2
   0x294F5C4: movk     x9, #0xbd4d, lsl #16 ; a9a9b7f2
   0x294F5C8: adrp     x8, #0x32e9000 ; c84c00d0
   0x294F5CC: add      x8, x8, #0x399 ; 08650e91
   0x294F5D0: movk     x9, #0xe9bd, lsl #32 ; a937ddf2
   0x294F5D4: movk     x9, #0xdb0f, lsl #48 ; e961fbf2
   0x294F5D8: stp      x9, x8, [sp, #0x120] ; e92312a9
   0x294F5DC: mov      w8, #8 ; 08018052
   0x294F5E0: stp      x8, xzr, [sp, #0x130] ; e87f13a9
   0x294F5E4: adrp     x0, #0x612c000 ; e0be01b0
   0x294F5E8: add      x0, x0, #0x800 ; 00002091
   0x294F5EC: sub      x8, x29, #0xc0 ; a80303d1
   0x294F5F0: add      x1, sp, #0x120 ; e1830491
   0x294F5F4: sub      x2, x29, #0x78 ; a2e301d1
   0x294F5F8: mov      w3, wzr ; e3031f2a
   0x294F5FC: bl       #0x410a30 ; 0d056b97
~~~

