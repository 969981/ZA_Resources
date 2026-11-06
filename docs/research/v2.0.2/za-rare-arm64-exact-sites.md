# Z-A v2.0.2 Rare mask 0x1FFFFFFF exact opcode contexts

> [!WARNING] STATIC CANDIDATES ONLY. A mask instruction does not prove EncountData.Rare reads or a runtime hook.

- main.elf SHA-256: 470d6e71e27744a65ac6f1f94587dd34d24e0e2c0da9fd912eb1db03ee848d4d
- Exact scanner site count: 5
- Instruction window: 0x100 bytes before and 0x100 bytes after.
- To confirm: trace operand register origin and TID/PID xor logic in the same function; verify runtime via GDB, not just opcode shape.

## Static PC 0xE28C54 (word 0x12007129)

- ELF file offset: 0xE2969C; opcode: AND; mask: 0x1FFFFFFF
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE28B54: fsqrt    v3.2s, v3.2s ; 63f8a12e
   0xE28B58: mov      v3.d[1], v3.d[0] ; 6304186e
   0xE28B5C: fdiv     v4.4s, v2.4s, v3.4s ; 44fc236e
   0xE28B60: mov      w10, #0x9680 ; 0ad09252
   0xE28B64: movk     w10, #0x4b18, lsl #16 ; 0a63a972
   0xE28B68: fsub     s10, s1, s0 ; 2a38201e
   0xE28B6C: dup      v0.2s, w10 ; 400d040e
   0xE28B70: mov      w11, #0xc5ac ; 8bb59852
   0xE28B74: movk     w11, #0x3727, lsl #16 ; ebe4a672
   0xE28B78: ldr      q2, [x9, #0x40] ; 2211c03d
   0xE28B7C: ldr      q3, [x9, #0x290] ; 23a5c03d
   0xE28B80: dup      v11.2s, w11 ; 6b0d040e
   0xE28B84: movi     v12.2s, #1 ; 2c04000f
   0xE28B88: str      q5, [sp, #0x80] ; e523803d
   0xE28B8C: ldr      q5, [x9, #0x240] ; 2591c03d
   0xE28B90: mov      w28, wzr ; fc031f2a
   0xE28B94: adrp     x26, #0x3302000 ; da2601d0
   0xE28B98: add      x26, x26, #0xfb8 ; 5ae33e91
   0xE28B9C: add      x8, x8, #0x10 ; 08410091
   0xE28BA0: mov      w27, #1 ; 3b008052
   0xE28BA4: stp      q4, q6, [sp, #0x60] ; e41b03ad
   0xE28BA8: str      q0, [sp, #0x50] ; e017803d
   0xE28BAC: dup      v0.2d, v2.d[0] ; 4004084e
   0xE28BB0: str      q3, [sp, #0x10] ; e307803d
   0xE28BB4: stp      q0, q5, [sp, #0x20] ; e01701ad
   0xE28BB8: b        #0xe28bcc ; 05000014
   0xE28BBC: nop       ; 1f2003d5
   0xE28BC0: ldur     x8, [x29, #-0xd0] ; a80353f8
   0xE28BC4: stp      q2, q3, [sp, #0x50] ; e28f02ad
   0xE28BC8: str      q29, [sp, #0x70] ; fd1f803d
   0xE28BCC: ldr      x8, [x8] ; 080140f9
   0xE28BD0: sub      x0, x29, #0xd0 ; a04303d1
   0xE28BD4: sub      x5, x29, #0x80 ; a50302d1
   0xE28BD8: mov      x1, x22 ; e10316aa
   0xE28BDC: mov      x2, x24 ; e20318aa
   0xE28BE0: mov      x3, x21 ; e30315aa
   0xE28BE4: mov      x4, x23 ; e40317aa
   0xE28BE8: blr      x8 ; 00013fd6
   0xE28BEC: ldur     q0, [x29, #-0x80] ; a003d83c
   0xE28BF0: ldr      q3, [sp, #0x50] ; e317c03d
   0xE28BF4: ldp      q4, q29, [sp, #0x60] ; e47743ad
   0xE28BF8: fsub     v1.4s, v29.4s, v0.4s ; a1d7a04e
   0xE28BFC: fmul     v1.4s, v4.4s, v1.4s ; 81dc216e
   0xE28C00: dup      v2.2s, v1.s[2] ; 2204140e
   0xE28C04: faddp    v1.2s, v1.2s, v1.2s ; 21d4212e
   0xE28C08: fadd     v1.2s, v1.2s, v2.2s ; 21d4220e
   0xE28C0C: fsub     v2.2s, v3.2s, v11.2s ; 62d4ab0e
   0xE28C10: fcmgt    v2.2s, v2.2s, v1.2s ; 42e4a12e
   0xE28C14: mvn      v2.8b, v2.8b ; 4258202e
   0xE28C18: fmov     w8, s2 ; 4800261e
   0xE28C1C: tbz      w8, #0, #0xe28c70 ; a8020036
   0xE28C20: cbz      x21, #0xe28c7c ; f50200b4
   0xE28C24: ldr      d0, [x20, #0x60] ; 803240fd
   0xE28C28: fmax     v0.2s, v11.2s, v0.2s ; 60f5200e
   0xE28C2C: ldr      d1, [x20, #0x50] ; 812a40fd
   0xE28C30: fsub     s1, s3, s1 ; 6138211e
   0xE28C34: ldr      q28, [sp, #0x80] ; fc23c03d
   0xE28C38: fcmp     s1, s0 ; 2020201e
   0xE28C3C: b.ls     #0xe295d0 ; a94c0054
   0xE28C40: ldr      d0, [x20, #0x50] ; 802a40fd
   0xE28C44: fsub     v1.2s, v3.2s, v0.2s ; 61d4a00e
   0xE28C48: fcmp     s1, #0.0 ; 2820201e
   0xE28C4C: b.gt     #0xe28c90 ; 2c020054
   0xE28C50: sub      w9, w28, #1 ; 89070051
>> 0xE28C54: and      w9, w9, #0x1fffffff ; 29710012
   0xE28C58: cmp      w9, #3 ; 3f0d0071
   0xE28C5C: str      q29, [sp, #0xf0] ; fd3f803d
   0xE28C60: str      q28, [sp, #0x80] ; fc23803d
   0xE28C64: b.ls     #0xe28cf4 ; 89040054
   0xE28C68: b        #0xe29528 ; 30020014
   0xE28C6C: nop       ; 1f2003d5
   0xE28C70: fmov     d3, d1 ; 2340601e
   0xE28C74: str      q0, [x25, w28, sxtw #4] ; 20dbbc3c
   0xE28C78: add      w28, w28, #1 ; 9c070011
   0xE28C7C: ldr      q28, [sp, #0x80] ; fc23c03d
   0xE28C80: ldr      d0, [x20, #0x50] ; 802a40fd
   0xE28C84: fsub     v1.2s, v3.2s, v0.2s ; 61d4a00e
   0xE28C88: fcmp     s1, #0.0 ; 2820201e
   0xE28C8C: b.le     #0xe28c50 ; 2dfeff54
   0xE28C90: ldr      q0, [x20] ; 8002c03d
   0xE28C94: fmul     v2.4s, v4.4s, v0.4s ; 82dc206e
   0xE28C98: dup      v3.2s, v2.s[2] ; 4304140e
   0xE28C9C: faddp    v2.2s, v2.2s, v2.2s ; 42d4222e
   0xE28CA0: fadd     v2.2s, v2.2s, v3.2s ; 42d4230e
   0xE28CA4: fcmp     s2, #0.0 ; 4820201e
   0xE28CA8: b.ge     #0xe295a4 ; ea470054
   0xE28CAC: fsub     v1.2s, v1.2s, v9.2s ; 21d4a90e
   0xE28CB0: fmax     v1.2s, v1.2s, v8.2s ; 21f4280e
   0xE28CB4: fdiv     v1.2s, v1.2s, v2.2s ; 21fc222e
   0xE28CB8: fsub     v28.2s, v28.2s, v1.2s ; 9cd7a10e
   0xE28CBC: fcmp     s28, s10 ; 80232a1e
   0xE28CC0: b.ge     #0xe295a4 ; 2a470054
   0xE28CC4: mov      v1.16b, v28.16b ; 811fbc4e
   0xE28CC8: mov      v1.d[1], v28.d[0] ; 8107186e
   0xE28CCC: fmul     v0.4s, v0.4s, v1.4s ; 00dc216e
   0xE28CD0: ldr      q1, [x20, #0x40] ; 8112c03d
   0xE28CD4: str      q4, [x19, #0x20] ; 640a803d
   0xE28CD8: fadd     v29.4s, v0.4s, v1.4s ; 1dd4214e
   0xE28CDC: sub      w9, w28, #1 ; 89070051
   0xE28CE0: and      w9, w9, #0x1fffffff ; 29710012
   0xE28CE4: cmp      w9, #3 ; 3f0d0071
   0xE28CE8: str      q29, [sp, #0xf0] ; fd3f803d
   0xE28CEC: str      q28, [sp, #0x80] ; fc23803d
   0xE28CF0: b.hi     #0xe29528 ; c8410054
   0xE28CF4: adr      x10, #0xe28d08 ; aa000010
   0xE28CF8: ldrh     w11, [x26, x9, lsl #1] ; 4b7b6978
   0xE28CFC: add      x10, x10, x11, lsl #2 ; 4a090b8b
   0xE28D00: mov      v2.16b, v29.16b ; a21fbd4e
   0xE28D04: br       x10 ; 40011fd6
   0xE28D08: ldr      q0, [sp, #0x90] ; e027c03d
   0xE28D0C: fsub     v4.4s, v0.4s, v2.4s ; 04d4a24e
   0xE28D10: str      q4, [sp, #0x180] ; e463803d
   0xE28D14: b        #0xe293fc ; ba010014
   0xE28D18: nop       ; 1f2003d5
   0xE28D1C: nop       ; 1f2003d5
   0xE28D20: ldp      q7, q0, [sp, #0xb0] ; e78345ad
   0xE28D24: mov      w9, #0xe6fe ; c9df9c52
   0xE28D28: movk     w9, #0x2edb, lsl #16 ; 69dba572
   0xE28D2C: ldr      q26, [sp, #0x20] ; fa0bc03d
   0xE28D30: fsub     v16.4s, v0.4s, v7.4s ; 10d4a74e
   0xE28D34: ext      v21.16b, v16.16b, v16.16b, #4 ; 1522106e
   0xE28D38: ldp      q4, q3, [sp, #0x90] ; e48f44ad
   0xE28D3C: fsub     v2.4s, v7.4s, v3.4s ; e2d4a34e
   0xE28D40: ext      v18.16b, v2.16b, v2.16b, #4 ; 5220026e
   0xE28D44: fsub     v1.4s, v0.4s, v3.4s ; 01d4a34e
   0xE28D48: ext      v19.16b, v1.16b, v1.16b, #4 ; 3320016e
   0xE28D4C: fsub     v17.4s, v4.4s, v7.4s ; 91d4a74e
   0xE28D50: fsub     v6.4s, v3.4s, v4.4s ; 66d4a44e
   0xE28D54: fsub     v5.4s, v0.4s, v4.4s ; 05d4a44e
~~~

## Static PC 0xE28CE0 (word 0x12007129)

- ELF file offset: 0xE29728; opcode: AND; mask: 0x1FFFFFFF
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0xE28BE0: mov      x3, x21 ; e30315aa
   0xE28BE4: mov      x4, x23 ; e40317aa
   0xE28BE8: blr      x8 ; 00013fd6
   0xE28BEC: ldur     q0, [x29, #-0x80] ; a003d83c
   0xE28BF0: ldr      q3, [sp, #0x50] ; e317c03d
   0xE28BF4: ldp      q4, q29, [sp, #0x60] ; e47743ad
   0xE28BF8: fsub     v1.4s, v29.4s, v0.4s ; a1d7a04e
   0xE28BFC: fmul     v1.4s, v4.4s, v1.4s ; 81dc216e
   0xE28C00: dup      v2.2s, v1.s[2] ; 2204140e
   0xE28C04: faddp    v1.2s, v1.2s, v1.2s ; 21d4212e
   0xE28C08: fadd     v1.2s, v1.2s, v2.2s ; 21d4220e
   0xE28C0C: fsub     v2.2s, v3.2s, v11.2s ; 62d4ab0e
   0xE28C10: fcmgt    v2.2s, v2.2s, v1.2s ; 42e4a12e
   0xE28C14: mvn      v2.8b, v2.8b ; 4258202e
   0xE28C18: fmov     w8, s2 ; 4800261e
   0xE28C1C: tbz      w8, #0, #0xe28c70 ; a8020036
   0xE28C20: cbz      x21, #0xe28c7c ; f50200b4
   0xE28C24: ldr      d0, [x20, #0x60] ; 803240fd
   0xE28C28: fmax     v0.2s, v11.2s, v0.2s ; 60f5200e
   0xE28C2C: ldr      d1, [x20, #0x50] ; 812a40fd
   0xE28C30: fsub     s1, s3, s1 ; 6138211e
   0xE28C34: ldr      q28, [sp, #0x80] ; fc23c03d
   0xE28C38: fcmp     s1, s0 ; 2020201e
   0xE28C3C: b.ls     #0xe295d0 ; a94c0054
   0xE28C40: ldr      d0, [x20, #0x50] ; 802a40fd
   0xE28C44: fsub     v1.2s, v3.2s, v0.2s ; 61d4a00e
   0xE28C48: fcmp     s1, #0.0 ; 2820201e
   0xE28C4C: b.gt     #0xe28c90 ; 2c020054
   0xE28C50: sub      w9, w28, #1 ; 89070051
   0xE28C54: and      w9, w9, #0x1fffffff ; 29710012
   0xE28C58: cmp      w9, #3 ; 3f0d0071
   0xE28C5C: str      q29, [sp, #0xf0] ; fd3f803d
   0xE28C60: str      q28, [sp, #0x80] ; fc23803d
   0xE28C64: b.ls     #0xe28cf4 ; 89040054
   0xE28C68: b        #0xe29528 ; 30020014
   0xE28C6C: nop       ; 1f2003d5
   0xE28C70: fmov     d3, d1 ; 2340601e
   0xE28C74: str      q0, [x25, w28, sxtw #4] ; 20dbbc3c
   0xE28C78: add      w28, w28, #1 ; 9c070011
   0xE28C7C: ldr      q28, [sp, #0x80] ; fc23c03d
   0xE28C80: ldr      d0, [x20, #0x50] ; 802a40fd
   0xE28C84: fsub     v1.2s, v3.2s, v0.2s ; 61d4a00e
   0xE28C88: fcmp     s1, #0.0 ; 2820201e
   0xE28C8C: b.le     #0xe28c50 ; 2dfeff54
   0xE28C90: ldr      q0, [x20] ; 8002c03d
   0xE28C94: fmul     v2.4s, v4.4s, v0.4s ; 82dc206e
   0xE28C98: dup      v3.2s, v2.s[2] ; 4304140e
   0xE28C9C: faddp    v2.2s, v2.2s, v2.2s ; 42d4222e
   0xE28CA0: fadd     v2.2s, v2.2s, v3.2s ; 42d4230e
   0xE28CA4: fcmp     s2, #0.0 ; 4820201e
   0xE28CA8: b.ge     #0xe295a4 ; ea470054
   0xE28CAC: fsub     v1.2s, v1.2s, v9.2s ; 21d4a90e
   0xE28CB0: fmax     v1.2s, v1.2s, v8.2s ; 21f4280e
   0xE28CB4: fdiv     v1.2s, v1.2s, v2.2s ; 21fc222e
   0xE28CB8: fsub     v28.2s, v28.2s, v1.2s ; 9cd7a10e
   0xE28CBC: fcmp     s28, s10 ; 80232a1e
   0xE28CC0: b.ge     #0xe295a4 ; 2a470054
   0xE28CC4: mov      v1.16b, v28.16b ; 811fbc4e
   0xE28CC8: mov      v1.d[1], v28.d[0] ; 8107186e
   0xE28CCC: fmul     v0.4s, v0.4s, v1.4s ; 00dc216e
   0xE28CD0: ldr      q1, [x20, #0x40] ; 8112c03d
   0xE28CD4: str      q4, [x19, #0x20] ; 640a803d
   0xE28CD8: fadd     v29.4s, v0.4s, v1.4s ; 1dd4214e
   0xE28CDC: sub      w9, w28, #1 ; 89070051
>> 0xE28CE0: and      w9, w9, #0x1fffffff ; 29710012
   0xE28CE4: cmp      w9, #3 ; 3f0d0071
   0xE28CE8: str      q29, [sp, #0xf0] ; fd3f803d
   0xE28CEC: str      q28, [sp, #0x80] ; fc23803d
   0xE28CF0: b.hi     #0xe29528 ; c8410054
   0xE28CF4: adr      x10, #0xe28d08 ; aa000010
   0xE28CF8: ldrh     w11, [x26, x9, lsl #1] ; 4b7b6978
   0xE28CFC: add      x10, x10, x11, lsl #2 ; 4a090b8b
   0xE28D00: mov      v2.16b, v29.16b ; a21fbd4e
   0xE28D04: br       x10 ; 40011fd6
   0xE28D08: ldr      q0, [sp, #0x90] ; e027c03d
   0xE28D0C: fsub     v4.4s, v0.4s, v2.4s ; 04d4a24e
   0xE28D10: str      q4, [sp, #0x180] ; e463803d
   0xE28D14: b        #0xe293fc ; ba010014
   0xE28D18: nop       ; 1f2003d5
   0xE28D1C: nop       ; 1f2003d5
   0xE28D20: ldp      q7, q0, [sp, #0xb0] ; e78345ad
   0xE28D24: mov      w9, #0xe6fe ; c9df9c52
   0xE28D28: movk     w9, #0x2edb, lsl #16 ; 69dba572
   0xE28D2C: ldr      q26, [sp, #0x20] ; fa0bc03d
   0xE28D30: fsub     v16.4s, v0.4s, v7.4s ; 10d4a74e
   0xE28D34: ext      v21.16b, v16.16b, v16.16b, #4 ; 1522106e
   0xE28D38: ldp      q4, q3, [sp, #0x90] ; e48f44ad
   0xE28D3C: fsub     v2.4s, v7.4s, v3.4s ; e2d4a34e
   0xE28D40: ext      v18.16b, v2.16b, v2.16b, #4 ; 5220026e
   0xE28D44: fsub     v1.4s, v0.4s, v3.4s ; 01d4a34e
   0xE28D48: ext      v19.16b, v1.16b, v1.16b, #4 ; 3320016e
   0xE28D4C: fsub     v17.4s, v4.4s, v7.4s ; 91d4a74e
   0xE28D50: fsub     v6.4s, v3.4s, v4.4s ; 66d4a44e
   0xE28D54: fsub     v5.4s, v0.4s, v4.4s ; 05d4a44e
   0xE28D58: ext      v23.16b, v5.16b, v5.16b, #4 ; b720056e
   0xE28D5C: mov      v19.d[1], v1.d[0] ; 3304186e
   0xE28D60: mov      v18.d[1], v2.d[0] ; 5204186e
   0xE28D64: mov      v21.d[1], v16.d[0] ; 1506186e
   0xE28D68: mov      v23.d[1], v5.d[0] ; b704186e
   0xE28D6C: fmul     v19.4s, v2.4s, v19.4s ; 53dc336e
   0xE28D70: fmul     v18.4s, v1.4s, v18.4s ; 32dc326e
   0xE28D74: fmul     v21.4s, v17.4s, v21.4s ; 35de356e
   0xE28D78: fmul     v23.4s, v6.4s, v23.4s ; d7dc376e
   0xE28D7C: fsub     v20.4s, v19.4s, v18.4s ; 74d6b24e
   0xE28D80: ext      v19.16b, v20.16b, v20.16b, #4 ; 9322146e
   0xE28D84: mov      v20.s[1], wzr ; f41f0c4e
   0xE28D88: mov      v18.16b, v19.16b ; 721eb34e
   0xE28D8C: mov      v18.d[1], v20.d[0] ; 9206186e
   0xE28D90: ext      v20.16b, v17.16b, v17.16b, #4 ; 3422116e
   0xE28D94: mov      v20.d[1], v17.d[0] ; 3406186e
   0xE28D98: fmul     v20.4s, v16.4s, v20.4s ; 14de346e
   0xE28D9C: fsub     v21.4s, v21.4s, v20.4s ; b5d6b44e
   0xE28DA0: ext      v22.16b, v21.16b, v21.16b, #4 ; b622156e
   0xE28DA4: mov      v21.s[1], wzr ; f51f0c4e
   0xE28DA8: mov      v20.16b, v22.16b ; d41eb64e
   0xE28DAC: fmul     v22.2s, v22.2s, v22.2s ; d6de362e
   0xE28DB0: mov      v20.d[1], v21.d[0] ; b406186e
   0xE28DB4: ext      v21.16b, v6.16b, v6.16b, #4 ; d520066e
   0xE28DB8: mov      v21.d[1], v6.d[0] ; d504186e
   0xE28DBC: fmul     v21.4s, v5.4s, v21.4s ; b5dc356e
   0xE28DC0: fsub     v21.4s, v23.4s, v21.4s ; f5d6b54e
   0xE28DC4: mov      v24.16b, v21.16b ; b81eb54e
   0xE28DC8: ext      v23.16b, v21.16b, v21.16b, #4 ; b722156e
   0xE28DCC: fmul     v21.2s, v21.2s, v21.2s ; b5de352e
   0xE28DD0: mov      v25.16b, v23.16b ; f91eb74e
   0xE28DD4: mov      v24.s[1], wzr ; f81f0c4e
   0xE28DD8: fmul     v23.2s, v23.2s, v23.2s ; f7de372e
   0xE28DDC: dup      v21.2s, v21.s[0] ; b506040e
   0xE28DE0: mov      v25.d[1], v24.d[0] ; 1907186e
~~~

## Static PC 0x1F01278 (word 0x1200714A)

- ELF file offset: 0x1F01CC0; opcode: AND; mask: 0x1FFFFFFF
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x1F01178: stp      x22, x21, [sp, #0x10] ; f65701a9
   0x1F0117C: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x1F01180: mov      x29, sp ; fd030091
   0x1F01184: mov      x19, x1 ; f30301aa
   0x1F01188: mov      x20, x0 ; f40300aa
   0x1F0118C: mov      x22, xzr ; f6031faa
   0x1F01190: adrp     x21, #0x32e3000 ; 159f00d0
   0x1F01194: add      x21, x21, #0x7e6 ; b59a1f91
   0x1F01198: ldrb     w3, [x20, x22] ; 836a7638
   0x1F0119C: mov      x0, x19 ; e00313aa
   0x1F011A0: mov      w1, #3 ; 61008052
   0x1F011A4: mov      x2, x21 ; e20315aa
   0x1F011A8: bl       #0x1ee48d8 ; cc8dff97
   0x1F011AC: add      x22, x22, #1 ; d6060091
   0x1F011B0: add      x19, x19, #2 ; 730a0091
   0x1F011B4: cmp      x22, #0x10 ; df4200f1
   0x1F011B8: b.ne     #0x1f01198 ; 01ffff54
   0x1F011BC: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x1F011C0: ldp      x22, x21, [sp, #0x10] ; f65741a9
   0x1F011C4: ldp      x29, x30, [sp], #0x30 ; fd7bc3a8
   0x1F011C8: ret       ; c0035fd6
   0x1F011CC: stp      x29, x30, [sp, #-0x30]! ; fd7bbda9
   0x1F011D0: stp      x22, x21, [sp, #0x10] ; f65701a9
   0x1F011D4: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x1F011D8: mov      x29, sp ; fd030091
   0x1F011DC: mov      x19, x1 ; f30301aa
   0x1F011E0: mov      x20, x0 ; f40300aa
   0x1F011E4: mov      x22, xzr ; f6031faa
   0x1F011E8: adrp     x21, #0x32e3000 ; 159f00d0
   0x1F011EC: add      x21, x21, #0x7e6 ; b59a1f91
   0x1F011F0: ldrb     w3, [x20, x22] ; 836a7638
   0x1F011F4: mov      x0, x19 ; e00313aa
   0x1F011F8: mov      w1, #3 ; 61008052
   0x1F011FC: mov      x2, x21 ; e20315aa
   0x1F01200: bl       #0x1ee48d8 ; b68dff97
   0x1F01204: add      x22, x22, #1 ; d6060091
   0x1F01208: add      x19, x19, #2 ; 730a0091
   0x1F0120C: cmp      x22, #0x20 ; df8200f1
   0x1F01210: b.ne     #0x1f011f0 ; 01ffff54
   0x1F01214: ldp      x20, x19, [sp, #0x20] ; f44f42a9
   0x1F01218: ldp      x22, x21, [sp, #0x10] ; f65741a9
   0x1F0121C: ldp      x29, x30, [sp], #0x30 ; fd7bc3a8
   0x1F01220: ret       ; c0035fd6
   0x1F01224: mov      x8, #0xdcfe ; c89f9bd2
   0x1F01228: movk     x8, #0x98ba, lsl #16 ; 4817b3f2
   0x1F0122C: movk     x8, #0x5476, lsl #32 ; c88ecaf2
   0x1F01230: movk     x8, #0x1032, lsl #48 ; 4806e2f2
   0x1F01234: str      x8, [x0, #0x10] ; 080800f9
   0x1F01238: mov      x8, #0x2301 ; 286084d2
   0x1F0123C: movk     x8, #0x6745, lsl #16 ; a8e8acf2
   0x1F01240: movk     x8, #0xab89, lsl #32 ; 2871d5f2
   0x1F01244: movk     x8, #0xefcd, lsl #48 ; a8f9fdf2
   0x1F01248: stp      xzr, x8, [x0] ; 1f2000a9
   0x1F0124C: ret       ; c0035fd6
   0x1F01250: stp      x29, x30, [sp, #-0x40]! ; fd7bbca9
   0x1F01254: str      x23, [sp, #0x10] ; f70b00f9
   0x1F01258: stp      x22, x21, [sp, #0x20] ; f65702a9
   0x1F0125C: stp      x20, x19, [sp, #0x30] ; f44f03a9
   0x1F01260: mov      x29, sp ; fd030091
   0x1F01264: ldp      w8, w9, [x0] ; 08244029
   0x1F01268: mov      w20, w2 ; f403022a
   0x1F0126C: mov      x19, x1 ; f30301aa
   0x1F01270: mov      x21, x0 ; f50300aa
   0x1F01274: add      w10, w8, w2 ; 0a01020b
>> 0x1F01278: and      w10, w10, #0x1fffffff ; 4a710012
   0x1F0127C: cmp      w10, w8 ; 5f01086b
   0x1F01280: and      x8, x8, #0x3f ; 08154092
   0x1F01284: cinc     w9, w9, lo ; 2925891a
   0x1F01288: add      w9, w9, w2, lsr #29 ; 2975420b
   0x1F0128C: stp      w10, w9, [x0] ; 0a240029
   0x1F01290: cbz      w8, #0x1f012e0 ; 88020034
   0x1F01294: mov      w9, #0x40 ; 09088052
   0x1F01298: sub      x22, x9, x8 ; 360108cb
   0x1F0129C: cmp      x22, w20, uxtw ; df4234eb
   0x1F012A0: b.ls     #0x1f012b4 ; a9000054
   0x1F012A4: add      x8, x21, x8 ; a802088b
   0x1F012A8: mov      w2, w20 ; e203142a
   0x1F012AC: add      x0, x8, #0x18 ; 00610091
   0x1F012B0: b        #0x1f01308 ; 16000014
   0x1F012B4: add      x23, x21, #0x18 ; b7620091
   0x1F012B8: mov      x1, x19 ; e10313aa
   0x1F012BC: mov      x2, x22 ; e20316aa
   0x1F012C0: add      x0, x23, x8 ; e002088b
   0x1F012C4: bl       #0x3161510 ; 93804994
   0x1F012C8: mov      x0, x21 ; e00315aa
   0x1F012CC: mov      x1, x23 ; e10317aa
   0x1F012D0: mov      w2, #0x40 ; 02088052
   0x1F012D4: add      x19, x19, x22 ; 7302168b
   0x1F012D8: sub      w20, w20, w22 ; 9402164b
   0x1F012DC: bl       #0x1f01640 ; d9000094
   0x1F012E0: cmp      w20, #0x40 ; 9f020171
   0x1F012E4: b.lo     #0x1f01300 ; e3000054
   0x1F012E8: and      w2, w20, #0xffffffc0 ; 82661a12
   0x1F012EC: mov      x0, x21 ; e00315aa
   0x1F012F0: mov      x1, x19 ; e10313aa
   0x1F012F4: bl       #0x1f01640 ; d3000094
   0x1F012F8: mov      x19, x0 ; f30300aa
   0x1F012FC: and      w20, w20, #0x3f ; 94160012
   0x1F01300: add      x0, x21, #0x18 ; a0620091
   0x1F01304: mov      w2, w20 ; e203142a
   0x1F01308: mov      x1, x19 ; e10313aa
   0x1F0130C: ldp      x20, x19, [sp, #0x30] ; f44f43a9
   0x1F01310: ldp      x22, x21, [sp, #0x20] ; f65742a9
   0x1F01314: ldr      x23, [sp, #0x10] ; f70b40f9
   0x1F01318: ldp      x29, x30, [sp], #0x40 ; fd7bc4a8
   0x1F0131C: b        #0x3161510 ; 7d804914
   0x1F01320: stp      x29, x30, [sp, #-0x30]! ; fd7bbda9
   0x1F01324: stp      x22, x21, [sp, #0x10] ; f65701a9
   0x1F01328: stp      x20, x19, [sp, #0x20] ; f44f02a9
   0x1F0132C: mov      x29, sp ; fd030091
   0x1F01330: mov      x21, x1 ; f50301aa
   0x1F01334: mov      x19, x1 ; f30301aa
   0x1F01338: mov      x20, x0 ; f40300aa
   0x1F0133C: ldr      w8, [x21], #0x18 ; a88641b8
   0x1F01340: and      x9, x8, #0x3f ; 09154092
   0x1F01344: mov      w8, #0x80 ; 08108052
   0x1F01348: eor      x22, x9, #0x3f ; 361540d2
   0x1F0134C: cmp      x22, #7 ; df1e00f1
   0x1F01350: strb     w8, [x21, x9] ; a86a2938
   0x1F01354: add      x8, x9, #1 ; 28050091
   0x1F01358: b.hi     #0x1f01388 ; 88010054
   0x1F0135C: add      x8, x19, x8 ; 6802088b
   0x1F01360: mov      w1, wzr ; e1031f2a
   0x1F01364: mov      x2, x22 ; e20316aa
   0x1F01368: add      x0, x8, #0x18 ; 00610091
   0x1F0136C: bl       #0x3161520 ; 6d804994
   0x1F01370: mov      x0, x19 ; e00313aa
   0x1F01374: mov      x1, x21 ; e10315aa
   0x1F01378: mov      w2, #0x40 ; 02088052
~~~

## Static PC 0x2E36644 (word 0x1200713C)

- ELF file offset: 0x2E3708C; opcode: AND; mask: 0x1FFFFFFF
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x2E36544: add      w12, w12, #1 ; 8c050011
   0x2E36548: add      x14, x14, x17 ; ce01118b
   0x2E3654C: tbz      w15, #0x1d, #0x2e36538 ; 6fffef36
   0x2E36550: add      x25, x9, w26, sxtw #2 ; 39c93a8b
   0x2E36554: ldr      x12, [x22, #0x30] ; cc1a40f9
   0x2E36558: asr      x9, x14, #0x1e ; c9fd5e93
   0x2E3655C: ldr      w13, [x25, #8]! ; 2d8f40b8
   0x2E36560: and      x14, x13, #0xfffffff ; ae6d4092
   0x2E36564: ldr      w9, [x25, x9] ; 296b69b8
   0x2E36568: add      x12, x12, x14, lsl #6 ; 8c190e8b
   0x2E3656C: tbnz     w13, #0x1c, #0x2e365a0 ; ad01e037
   0x2E36570: ldp      x14, x13, [x12, #0x10] ; 8e3541a9
   0x2E36574: ldr      x15, [x12, #8] ; 8f0540f9
   0x2E36578: stp      x15, x14, [sp, #0x68] ; efbb06a9
   0x2E3657C: str      x13, [sp, #0x78] ; ed3f00f9
   0x2E36580: ldr      x16, [sp, #0x50] ; f02b40f9
   0x2E36584: ldr      x13, [x12] ; 8d0140f9
   0x2E36588: str      x13, [sp, #0x60] ; ed3300f9
   0x2E3658C: ldp      x13, x14, [x12, #0x30] ; 8d3943a9
   0x2E36590: ldp      x12, x15, [x12, #0x20] ; 8c3d42a9
   0x2E36594: stp      x13, x14, [x16, #0x10] ; 0d3a01a9
   0x2E36598: stp      x12, x15, [x16] ; 0c3e00a9
   0x2E3659C: b        #0x2e36624 ; 22000014
   0x2E365A0: ldp      q0, q1, [x12] ; 800540ad
   0x2E365A4: ldr      q2, [sp, #0x40] ; e213c03d
   0x2E365A8: and      v0.16b, v0.16b, v2.16b ; 001c224e
   0x2E365AC: fmov     x14, d1 ; 2e00669e
   0x2E365B0: mov      x13, v1.d[1] ; 2d3c184e
   0x2E365B4: neg      v0.2d, v0.2d ; 00b8e06e
   0x2E365B8: extr     x15, x14, x13, #0xb ; cf2dcd93
   0x2E365BC: and      x14, x14, #0xffffffffffffc000 ; cec57292
   0x2E365C0: str      q0, [sp, #0x60] ; e01b803d
   0x2E365C4: bfi      x13, x15, #0xb, #0x35 ; edd175b3
   0x2E365C8: lsr      x15, x15, #0x35 ; effd75d3
   0x2E365CC: mvn      w15, w15 ; ef032f2a
   0x2E365D0: mvn      x16, x13 ; f0032daa
   0x2E365D4: neg      x13, x13 ; ed030dcb
   0x2E365D8: cmp      x13, x16 ; bf0110eb
   0x2E365DC: cinc     w15, w15, lo ; ef258f1a
   0x2E365E0: extr     x15, x15, x13, #0xb ; ef2dcd93
   0x2E365E4: bfi      x13, x15, #0xb, #0x35 ; edd175b3
   0x2E365E8: lsr      x15, x15, #0x35 ; effd75d3
   0x2E365EC: sub      x14, x15, x14 ; ee010ecb
   0x2E365F0: stp      x14, x13, [sp, #0x70] ; ee3707a9
   0x2E365F4: ldr      d0, [x12, #0x20] ; 801140fd
   0x2E365F8: fneg     d0, d0 ; 0040611e
   0x2E365FC: str      d0, [sp, #0x80] ; e04300fd
   0x2E36600: ldr      d0, [x12, #0x28] ; 801540fd
   0x2E36604: fneg     d0, d0 ; 0040611e
   0x2E36608: str      d0, [sp, #0x88] ; e04700fd
   0x2E3660C: ldr      d0, [x12, #0x30] ; 801940fd
   0x2E36610: fneg     d0, d0 ; 0040611e
   0x2E36614: str      d0, [sp, #0x90] ; e04b00fd
   0x2E36618: ldr      d0, [x12, #0x38] ; 801d40fd
   0x2E3661C: fneg     d0, d0 ; 0040611e
   0x2E36620: str      d0, [sp, #0x98] ; e04f00fd
   0x2E36624: sub      x10, x10, #2 ; 4a0900d1
   0x2E36628: tst      x10, #0xfffffffe ; 5f797ff2
   0x2E3662C: b.eq     #0x2e369ec ; 001e0054
   0x2E36630: and      x8, x11, #0x7fffffff ; 68794092
   0x2E36634: tst      x11, #0x7ffffffe ; 7f757ff2
   0x2E36638: mov      x19, xzr ; f3031faa
   0x2E3663C: csinc    x8, x8, xzr, ne ; 08159f9a
   0x2E36640: mov      x27, xzr ; fb031faa
>> 0x2E36644: and      w28, w9, #0x1fffffff ; 3c710012
   0x2E36648: lsl      x8, x8, #1 ; 08f97fd3
   0x2E3664C: str      x8, [sp, #0x38] ; e81f00f9
   0x2E36650: asr      x8, x19, #0x1e ; 68fe5e93
   0x2E36654: ldr      x9, [x22, #0x30] ; c91a40f9
   0x2E36658: and      w10, w28, #0xfffffff ; 8a6f0012
   0x2E3665C: orr      x8, x8, #4 ; 08017eb2
   0x2E36660: ldr      w8, [x25, x8] ; 286b68b8
   0x2E36664: add      x9, x9, x10, lsl #6 ; 29190a8b
   0x2E36668: lsr      w10, w28, #0x1c ; 8a7f1c53
   0x2E3666C: cbnz     w10, #0x2e366a4 ; ca010035
   0x2E36670: ldp      x11, x10, [x9, #0x10] ; 2b2941a9
   0x2E36674: ldr      x12, [x9, #8] ; 2c0540f9
   0x2E36678: ldr      x13, [sp, #0x28] ; ed1740f9
   0x2E3667C: stp      x12, x11, [x13, #8] ; acad00a9
   0x2E36680: str      x10, [x13, #0x18] ; aa0d00f9
   0x2E36684: ldr      x10, [x9] ; 2a0140f9
   0x2E36688: str      x10, [x13] ; aa0100f9
   0x2E3668C: ldur     x13, [x29, #-8] ; ad835ff8
   0x2E36690: ldp      x10, x11, [x9, #0x30] ; 2a2d43a9
   0x2E36694: ldp      x9, x12, [x9, #0x20] ; 293142a9
   0x2E36698: stp      x10, x11, [x13, #0x10] ; aa2d01a9
   0x2E3669C: stp      x9, x12, [x13] ; a93100a9
   0x2E366A0: b        #0x2e36728 ; 22000014
   0x2E366A4: ldp      q0, q1, [x9] ; 200540ad
   0x2E366A8: ldr      q2, [sp, #0x40] ; e213c03d
   0x2E366AC: and      v0.16b, v0.16b, v2.16b ; 001c224e
   0x2E366B0: fmov     x11, d1 ; 2b00669e
   0x2E366B4: mov      x10, v1.d[1] ; 2a3c184e
   0x2E366B8: neg      v0.2d, v0.2d ; 00b8e06e
   0x2E366BC: extr     x12, x11, x10, #0xb ; 6c2dca93
   0x2E366C0: and      x11, x11, #0xffffffffffffc000 ; 6bc57292
   0x2E366C4: str      q0, [sp, #0xa0] ; e02b803d
   0x2E366C8: bfi      x10, x12, #0xb, #0x35 ; 8ad175b3
   0x2E366CC: lsr      x12, x12, #0x35 ; 8cfd75d3
   0x2E366D0: mvn      w12, w12 ; ec032c2a
   0x2E366D4: mvn      x13, x10 ; ed032aaa
   0x2E366D8: neg      x10, x10 ; ea030acb
   0x2E366DC: cmp      x10, x13 ; 5f010deb
   0x2E366E0: cinc     w12, w12, lo ; 8c258c1a
   0x2E366E4: extr     x12, x12, x10, #0xb ; 8c2dca93
   0x2E366E8: bfi      x10, x12, #0xb, #0x35 ; 8ad175b3
   0x2E366EC: lsr      x12, x12, #0x35 ; 8cfd75d3
   0x2E366F0: sub      x11, x12, x11 ; 8b010bcb
   0x2E366F4: stp      x11, x10, [sp, #0xb0] ; eb2b0ba9
   0x2E366F8: ldr      d0, [x9, #0x20] ; 201140fd
   0x2E366FC: fneg     d0, d0 ; 0040611e
   0x2E36700: str      d0, [sp, #0xc0] ; e06300fd
   0x2E36704: ldr      d0, [x9, #0x28] ; 201540fd
   0x2E36708: fneg     d0, d0 ; 0040611e
   0x2E3670C: str      d0, [sp, #0xc8] ; e06700fd
   0x2E36710: ldr      d0, [x9, #0x30] ; 201940fd
   0x2E36714: fneg     d0, d0 ; 0040611e
   0x2E36718: str      d0, [sp, #0xd0] ; e06b00fd
   0x2E3671C: ldr      d0, [x9, #0x38] ; 201d40fd
   0x2E36720: fneg     d0, d0 ; 0040611e
   0x2E36724: str      d0, [sp, #0xd8] ; e06f00fd
   0x2E36728: ldr      x9, [x22, #0x30] ; c91a40f9
   0x2E3672C: and      w28, w8, #0x1fffffff ; 1c710012
   0x2E36730: and      x8, x8, #0xfffffff ; 086d4092
   0x2E36734: add      x8, x9, x8, lsl #6 ; 2819088b
   0x2E36738: lsr      w9, w28, #0x1c ; 897f1c53
   0x2E3673C: cbnz     w9, #0x2e36774 ; c9010035
   0x2E36740: ldp      x10, x9, [x8, #0x10] ; 0a2541a9
   0x2E36744: ldr      x11, [x8, #8] ; 0b0540f9
~~~

## Static PC 0x2E3672C (word 0x1200711C)

- ELF file offset: 0x2E37174; opcode: AND; mask: 0x1FFFFFFF
- NOT VERIFIED: register source, function identity, execution, game-state conditions, PID branch.

~~~asm
   0x2E3662C: b.eq     #0x2e369ec ; 001e0054
   0x2E36630: and      x8, x11, #0x7fffffff ; 68794092
   0x2E36634: tst      x11, #0x7ffffffe ; 7f757ff2
   0x2E36638: mov      x19, xzr ; f3031faa
   0x2E3663C: csinc    x8, x8, xzr, ne ; 08159f9a
   0x2E36640: mov      x27, xzr ; fb031faa
   0x2E36644: and      w28, w9, #0x1fffffff ; 3c710012
   0x2E36648: lsl      x8, x8, #1 ; 08f97fd3
   0x2E3664C: str      x8, [sp, #0x38] ; e81f00f9
   0x2E36650: asr      x8, x19, #0x1e ; 68fe5e93
   0x2E36654: ldr      x9, [x22, #0x30] ; c91a40f9
   0x2E36658: and      w10, w28, #0xfffffff ; 8a6f0012
   0x2E3665C: orr      x8, x8, #4 ; 08017eb2
   0x2E36660: ldr      w8, [x25, x8] ; 286b68b8
   0x2E36664: add      x9, x9, x10, lsl #6 ; 29190a8b
   0x2E36668: lsr      w10, w28, #0x1c ; 8a7f1c53
   0x2E3666C: cbnz     w10, #0x2e366a4 ; ca010035
   0x2E36670: ldp      x11, x10, [x9, #0x10] ; 2b2941a9
   0x2E36674: ldr      x12, [x9, #8] ; 2c0540f9
   0x2E36678: ldr      x13, [sp, #0x28] ; ed1740f9
   0x2E3667C: stp      x12, x11, [x13, #8] ; acad00a9
   0x2E36680: str      x10, [x13, #0x18] ; aa0d00f9
   0x2E36684: ldr      x10, [x9] ; 2a0140f9
   0x2E36688: str      x10, [x13] ; aa0100f9
   0x2E3668C: ldur     x13, [x29, #-8] ; ad835ff8
   0x2E36690: ldp      x10, x11, [x9, #0x30] ; 2a2d43a9
   0x2E36694: ldp      x9, x12, [x9, #0x20] ; 293142a9
   0x2E36698: stp      x10, x11, [x13, #0x10] ; aa2d01a9
   0x2E3669C: stp      x9, x12, [x13] ; a93100a9
   0x2E366A0: b        #0x2e36728 ; 22000014
   0x2E366A4: ldp      q0, q1, [x9] ; 200540ad
   0x2E366A8: ldr      q2, [sp, #0x40] ; e213c03d
   0x2E366AC: and      v0.16b, v0.16b, v2.16b ; 001c224e
   0x2E366B0: fmov     x11, d1 ; 2b00669e
   0x2E366B4: mov      x10, v1.d[1] ; 2a3c184e
   0x2E366B8: neg      v0.2d, v0.2d ; 00b8e06e
   0x2E366BC: extr     x12, x11, x10, #0xb ; 6c2dca93
   0x2E366C0: and      x11, x11, #0xffffffffffffc000 ; 6bc57292
   0x2E366C4: str      q0, [sp, #0xa0] ; e02b803d
   0x2E366C8: bfi      x10, x12, #0xb, #0x35 ; 8ad175b3
   0x2E366CC: lsr      x12, x12, #0x35 ; 8cfd75d3
   0x2E366D0: mvn      w12, w12 ; ec032c2a
   0x2E366D4: mvn      x13, x10 ; ed032aaa
   0x2E366D8: neg      x10, x10 ; ea030acb
   0x2E366DC: cmp      x10, x13 ; 5f010deb
   0x2E366E0: cinc     w12, w12, lo ; 8c258c1a
   0x2E366E4: extr     x12, x12, x10, #0xb ; 8c2dca93
   0x2E366E8: bfi      x10, x12, #0xb, #0x35 ; 8ad175b3
   0x2E366EC: lsr      x12, x12, #0x35 ; 8cfd75d3
   0x2E366F0: sub      x11, x12, x11 ; 8b010bcb
   0x2E366F4: stp      x11, x10, [sp, #0xb0] ; eb2b0ba9
   0x2E366F8: ldr      d0, [x9, #0x20] ; 201140fd
   0x2E366FC: fneg     d0, d0 ; 0040611e
   0x2E36700: str      d0, [sp, #0xc0] ; e06300fd
   0x2E36704: ldr      d0, [x9, #0x28] ; 201540fd
   0x2E36708: fneg     d0, d0 ; 0040611e
   0x2E3670C: str      d0, [sp, #0xc8] ; e06700fd
   0x2E36710: ldr      d0, [x9, #0x30] ; 201940fd
   0x2E36714: fneg     d0, d0 ; 0040611e
   0x2E36718: str      d0, [sp, #0xd0] ; e06b00fd
   0x2E3671C: ldr      d0, [x9, #0x38] ; 201d40fd
   0x2E36720: fneg     d0, d0 ; 0040611e
   0x2E36724: str      d0, [sp, #0xd8] ; e06f00fd
   0x2E36728: ldr      x9, [x22, #0x30] ; c91a40f9
>> 0x2E3672C: and      w28, w8, #0x1fffffff ; 1c710012
   0x2E36730: and      x8, x8, #0xfffffff ; 086d4092
   0x2E36734: add      x8, x9, x8, lsl #6 ; 2819088b
   0x2E36738: lsr      w9, w28, #0x1c ; 897f1c53
   0x2E3673C: cbnz     w9, #0x2e36774 ; c9010035
   0x2E36740: ldp      x10, x9, [x8, #0x10] ; 0a2541a9
   0x2E36744: ldr      x11, [x8, #8] ; 0b0540f9
   0x2E36748: ldr      x12, [sp, #0x20] ; ec1340f9
   0x2E3674C: stp      x11, x10, [x12, #8] ; 8ba900a9
   0x2E36750: str      x9, [x12, #0x18] ; 890d00f9
   0x2E36754: ldr      x9, [x8] ; 090140f9
   0x2E36758: str      x9, [x12] ; 890100f9
   0x2E3675C: ldr      x12, [sp, #0x58] ; ec2f40f9
   0x2E36760: ldp      x9, x10, [x8, #0x30] ; 092943a9
   0x2E36764: ldp      x8, x11, [x8, #0x20] ; 082d42a9
   0x2E36768: stp      x9, x10, [x12, #0x10] ; 892901a9
   0x2E3676C: stp      x8, x11, [x12] ; 882d00a9
   0x2E36770: b        #0x2e367f8 ; 22000014
   0x2E36774: ldp      q0, q1, [x8] ; 000540ad
   0x2E36778: ldr      q2, [sp, #0x40] ; e213c03d
   0x2E3677C: and      v0.16b, v0.16b, v2.16b ; 001c224e
   0x2E36780: fmov     x10, d1 ; 2a00669e
   0x2E36784: mov      x9, v1.d[1] ; 293c184e
   0x2E36788: neg      v0.2d, v0.2d ; 00b8e06e
   0x2E3678C: extr     x11, x10, x9, #0xb ; 4b2dc993
   0x2E36790: and      x10, x10, #0xffffffffffffc000 ; 4ac57292
   0x2E36794: str      q0, [sp, #0xe0] ; e03b803d
   0x2E36798: bfi      x9, x11, #0xb, #0x35 ; 69d175b3
   0x2E3679C: lsr      x11, x11, #0x35 ; 6bfd75d3
   0x2E367A0: mvn      w11, w11 ; eb032b2a
   0x2E367A4: mvn      x12, x9 ; ec0329aa
   0x2E367A8: neg      x9, x9 ; e90309cb
   0x2E367AC: cmp      x9, x12 ; 3f010ceb
   0x2E367B0: cinc     w11, w11, lo ; 6b258b1a
   0x2E367B4: extr     x11, x11, x9, #0xb ; 6b2dc993
   0x2E367B8: bfi      x9, x11, #0xb, #0x35 ; 69d175b3
   0x2E367BC: lsr      x11, x11, #0x35 ; 6bfd75d3
   0x2E367C0: sub      x10, x11, x10 ; 6a010acb
   0x2E367C4: stp      x10, x9, [sp, #0xf0] ; ea270fa9
   0x2E367C8: ldr      d0, [x8, #0x20] ; 001140fd
   0x2E367CC: fneg     d0, d0 ; 0040611e
   0x2E367D0: str      d0, [sp, #0x100] ; e08300fd
   0x2E367D4: ldr      d0, [x8, #0x28] ; 001540fd
   0x2E367D8: fneg     d0, d0 ; 0040611e
   0x2E367DC: str      d0, [sp, #0x108] ; e08700fd
   0x2E367E0: ldr      d0, [x8, #0x30] ; 001940fd
   0x2E367E4: fneg     d0, d0 ; 0040611e
   0x2E367E8: str      d0, [sp, #0x110] ; e08b00fd
   0x2E367EC: ldr      d0, [x8, #0x38] ; 001d40fd
   0x2E367F0: fneg     d0, d0 ; 0040611e
   0x2E367F4: str      d0, [sp, #0x118] ; e08f00fd
   0x2E367F8: ldr      x24, [x21, #0x30] ; b81a40f9
   0x2E367FC: mov      x22, x21 ; f60315aa
   0x2E36800: ldp      w21, w8, [x24, #0x20] ; 15234429
   0x2E36804: sxtw     x21, w21 ; b57e4093
   0x2E36808: add      x23, x21, #1 ; b7060091
   0x2E3680C: and      w8, w8, #0x7fffffff ; 08790012
   0x2E36810: cmp      w8, w21 ; 1f01156b
   0x2E36814: b.gt     #0x2e36828 ; ac000054
   0x2E36818: add      x0, x24, #0x18 ; 00630091
   0x2E3681C: mov      x1, x23 ; e10317aa
   0x2E36820: bl       #0x2e37370 ; d4020094
   0x2E36824: ldr      w21, [x24, #0x20] ; 152340b9
   0x2E36828: ldp      x0, x2, [sp, #0x50] ; e00b45a9
   0x2E3682C: add      x3, sp, #0x120 ; e3830491
~~~

