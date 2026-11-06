#!/usr/bin/env python3
"""AArch64 main.elf rare / PID read-only audit; candidates != proof of shiny lock."""
from __future__ import annotations
import argparse, bisect, csv, hashlib, importlib.util, json, struct
from pathlib import Path

ROM = Path('Unpack/v2.0.2')
ELF = ROM / 'exefs/main/main.elf'
MANIFEST = ROM / 'exefs/exefs-manifest.json'
SCHEMA = ROM / 'romfs/arc/data.trpfs/virtual/world/ik_data/field/pokemon/encount_data/encount_data/encount_data_array.bfbs'
FUNCTIONS = {'PID_Get': 0xE4DBE0, 'PID_Set': 0xE57350, 'TID_Get': 0xE49D50,
             'Species_Get': 0xE49940, 'IV_Get_HP': 0xE4BCF0, 'Personal_Load': 0xE380C0,
             'Shiny_CheckCandidate': 0xE5D1E8, 'Shiny_ModeClassifierCandidate': 0xE5D244,
             'Shiny_ModeSetterCandidate': 0xE46024, 'Shiny_ModeCheckCandidate': 0xE45F7C,
             'PID_ToShinyCandidate': 0xE5D21C, 'PID_ModeAdjustCandidate': 0xE5D284}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()

def section(blob, wanted='.text'):
    if blob[:4] != b'\x7fELF' or blob[4:6] != b'\x02\x01':
        raise ValueError('Expected ELF64 LE')
    if struct.unpack_from('<H',blob,18)[0] != 183:raise ValueError('Not AArch64')
    off=struct.unpack_from('<Q',blob,40)[0]
    entsize,n,ni=struct.unpack_from('<HHH',blob,58)
    if entsize!=64 or not n or off+n*entsize>len(blob):raise ValueError('Bad ELF section header')
    hs=[struct.unpack_from('<IIQQQQIIQQ',blob,off+i*64) for i in range(n)]
    tab=blob[hs[ni][4]:hs[ni][4]+hs[ni][5]]
    for row in hs:
        start=tab.find(b'\0',row[0]);name=tab[row[0]:start].decode('utf8','replace')
        if name==wanted:
            pos,size,virt=row[4],row[5],row[3]
            if pos+size>len(blob):raise ValueError('Bad section bounds')
            return virt,blob[pos:pos+size]
    raise ValueError('No section '+wanted)

def fields(repo):
    spec=importlib.util.spec_from_file_location('za_reflect',repo/'scripts/Export-ZA-Databases.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    r=mod.Reflection((repo/SCHEMA).read_bytes())
    return [{'object':o['name'],'name':f['name'],'fieldId':f['id'],
             'vtableSlotByteOffset':4+2*f['id'],'typeBase':f['base']}
            for o in r.objects for f in o['fields'] if 'rare' in f['name'].lower()]

def csvwrite(path,head,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(head);w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,default=Path('.'))
    ap.add_argument('--out',type=Path,default=Path('docs/research/ZA-v2.0.2/rare-arm64'))
    args=ap.parse_args()
    root=args.repo.resolve();out=(args.out if args.out.is_absolute() else root/args.out)
    out.mkdir(parents=True,exist_ok=True)
    m=json.loads((root/MANIFEST).read_text())
    digest=sha(root/ELF)
    if digest.lower()!=m['modules']['main']['elfSha256'].lower():
        raise ValueError('main.elf SHA-256 does not match repository manifest')
    elf_blob=(root/ELF).read_bytes()
    textva,code=section(elf_blob)
    if len(code)%4:raise ValueError('unaligned AArch64 .text')
    end=textva+len(code)
    if not all(textva <= p < end for p in FUNCTIONS.values()):
        raise ValueError('External reference RVA not in main.elf text')
    from capstone import Cs,CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN
    md=Cs(CS_ARCH_ARM64,CS_MODE_LITTLE_ENDIAN)
    def context(at,before=10,after=17):
        start=max(textva,at-before*4);stop=min(end,at+(after+1)*4)
        part=code[start-textva:stop-textva]
        return '\n'.join(('>>' if x.address==at else '  ')+
                         f' main+0x{x.address:X}: {x.mnemonic} {x.op_str}'
                         for x in md.disasm(part,start))
    reverse={v:[] for v in FUNCTIONS.values()};tails={v:[] for v in FUNCTIONS.values()};msb_tests=[];shifts=[];literal={v:[] for v in (0x1FFFFFFF,0x2FFFFFFF,0x3FFFFFFF)}
    for i,(w,) in enumerate(struct.iter_unpack('<I',code)):
        pc=textva+i*4
        if w&0xFC000000==0x94000000:
            imm=w&0x03FFFFFF
            if imm&(1<<25):imm-=1<<26
            target=pc+imm*4
            if target in reverse:reverse[target].append(pc)
        # B imm26: compiler uses tail-call B as well as BL to setter helpers.
        if w&0xFC000000==0x14000000:
            imm=w&0x03FFFFFF
            if imm&(1<<25):imm-=1<<26
            target=pc+imm*4
            if target in tails:tails[target].append(pc)
        # TBZ/TBNZ of high rare mode bits 28..31, candidate only.
        if w&0x7E000000==0x36000000:
            bit=((w>>31)&1)*32+((w>>19)&31)
            if bit in (28,29,30,31):msb_tests.append((pc,bit))
        if w&0x7F800000==0x53000000:
            if (w>>16)&63==28 and (w>>10)&63 in (31,63):shifts.append(pc)
        if w in literal:literal[w].append(pc)
    pidcalls=sorted(reverse[FUNCTIONS['PID_Set']]);candidates=[]
    for pc in shifts:
        dis=list(md.disasm(code[max(0,pc-textva-40):min(len(code),pc-textva+124)],max(textva,pc-40)))
        comp=[f'{x.mnemonic} {x.op_str}' for x in dis
              if x.mnemonic in ('cmp','subs','ccmp','tst') and any(z in x.op_str for z in ('#0x1','#0x2','#0x3','#1','#2','#3'))]
        j=bisect.bisect_left(pidcalls,pc)
        near=min([abs(pidcalls[k]-pc) for k in (j-1,j) if 0<=k<len(pidcalls)] or [2147483647])
        score=10*bool(comp)+5*(near<4096)+2*(near<16384)
        candidates.append((score,near,pc,'; '.join(comp[:10]),context(pc)))
    candidates.sort(key=lambda v:(-v[0],v[1],v[2]))
    csvwrite(out/'shift28-candidates.csv',
        ['rva','heuristicScore','distanceToNearestPIDSetterBL','nearbyCompare','context','classification'],
        [[f'0x{pc:X}',score,dist,comp,ctx,'candidate_UNVERIFIED_rare']
         for score,dist,pc,comp,ctx in candidates[:500]])
    csvwrite(out/'pid-direct-callers.csv',
        ['reference','targetRva','blCallsiteRva','context','classification'],
        [[name,f'0x{target:X}',f'0x{pc:X}',context(pc),'direct_BL_not_shiny_proof']
         for name,target in FUNCTIONS.items() for pc in reverse[target][:5000]])
    csvwrite(out/'pid-tail-branches.csv',
        ['target','targetRva','tailBranchRva','context','classification'],
        [[name,f'0x{target:X}',f'0x{pc:X}',context(pc),
          'direct_B_tail_call_NOT_shiny_proof']
         for name,target in FUNCTIONS.items() for pc in tails[target]])
    ranked_tests=sorted(msb_tests,
        key=lambda x:(abs(x[0]-0xE45FD0),x[0]))
    csvwrite(out/'rare-highbit-tests.csv',
        ['rva','bitIndex','distanceFromKnownPIDTIDChecksBytes','context','classification'],
        [[f'0x{pc:X}',bit,abs(pc-0xE45FD0),context(pc),
          'TBZ_TBNZ_high_bit_candidate_NOT_rare_proof']
         for pc,bit in ranked_tests[:250]])
    windows=[
       ('PID_TID_check_neighborhood',0xE45F70,0xE46190),
       ('PID_TID_shiny_math_helpers',0xE5D1E8,0xE5D2D0),
       ('PID_shiny_mode_setter',0xE46024,0xE46138),
       ('PID_creation_setter_context',0xE3EB20,0xE3EC30),
       ('PID_setter_entry',0xE57350,0xE57434),
    ]
    trace=['# Z-A 2.0.2 PID/TID/闪光相关候选函数反汇编','',
           '> 所有指令来自与 manifest SHA 匹配的 main.elf；'
           '以下函数名为研究用标签，不保证全是生成或锁闪函数。','']
    for label,a,b in windows:
        if a<textva or b>end:continue
        trace += ['## '+label+f'  main+0x{a:X}..0x{b:X}','',
                  '~~~asm']
        trace += [f'main+0x{x.address:X}: {x.mnemonic} {x.op_str}'
                  for x in md.disasm(code[a-textva:b-textva],a)]
        trace += ['~~~','']
    (out/'pid-shiny-function-windows.md').write_text(
        '\n'.join(trace),encoding='utf-8')
    # Find actual 64-bit pointers to virtual method thunks (if relocated
    # addresses are stored as image-relative 64-bit ELF pointer constants).
    def section_ranges():
        eoff=struct.unpack_from('<Q',elf_blob,40)[0]
        cnt,idx=struct.unpack_from('<HH',elf_blob,60)
        hdrs=[struct.unpack_from('<IIQQQQIIQQ',elf_blob,eoff+i*64) for i in range(cnt)]
        strings=elf_blob[hdrs[idx][4]:hdrs[idx][4]+hdrs[idx][5]]
        result=[]
        for item in hdrs:
            ni=item[0];j=strings.find(b'\0',ni)
            if j<0:continue
            name=strings[ni:j].decode('utf8','replace')
            result.append((name,item[4],item[4]+item[5],item[3]))
        return result
    ranges=section_ranges()
    pointer_targets={
        'mode_setter_wrapper_a':0x2D7008C,
        'mode_setter_wrapper_b':0x2D755E4,
        'mode_checker_wrapper_a':0x2D70084,
        'mode_checker_wrapper_b':0x2D755D4,
        'mode_setter_core':0xE46024,
        'mode_checker_core':0xE45F7C,
        'shiny_xor_helper':0xE5D1E8,
    }
    pointer_hits=[]
    for name,value in pointer_targets.items():
        needle=struct.pack('<Q',value)
        pos=0
        while True:
            pos=elf_blob.find(needle,pos)
            if pos<0:break
            origin=next(((sect,va+pos-lo)
                         for sect,lo,hi,va in ranges
                         if lo<=pos<hi),('UNKNOWN',None))
            pointer_hits.append([
                name,f'0x{value:X}',f'0x{pos:X}',origin[0],
                f'0x{origin[1]:X}' if origin[1] is not None else '',
                'ELF_pointer_literal_NOT_confirmed_vtable_slot'
            ])
            pos+=8
    csvwrite(out/'shiny-function-pointer-xrefs.csv',
        ['targetName','targetRva','elfFileOffset','section','pointerImageRva','classification'],
        pointer_hits)
    vtable_summary={}
    # Public source: PokemonParam wrapper vtable at main+0x3E28E58.
    vtable_base=0x3E28E58
    for name,lo,hi,va in ranges:
        if va<=vtable_base<va+(hi-lo):
            byte=lo+(vtable_base-va)
            possible=[]
            for slot in range(321):
                p=byte+slot*8
                if p+8>hi:break
                val=struct.unpack_from('<Q',elf_blob,p)[0]
                if val in pointer_targets.values():
                    possible.append({'slot':slot,'ptr':f'0x{val:X}',
                                     'targetName':[k for k,v in pointer_targets.items() if v==val][0]})
            vtable_summary={'baseRva':f'0x{vtable_base:X}','section':name,
                            'numberOfSlotsChecked':321,'knownFunctionPointers':possible}
            break
    # ELF may hold vtable function pointers as addends of AArch64 RELA
    # relocations, not as initialized .data values. Detect R_AARCH64_RELATIVE
    # entries only when complete r_offset, r_info, r_addend triples match.
    relocs=[]
    for name,val in pointer_targets.items():
        needle=struct.pack('<q',val)
        start=0
        while True:
            k=elf_blob.find(needle,start)
            if k<0:break
            if k>=16:
                r_off,r_info=struct.unpack_from('<QQ',elf_blob,k-16)
                relocation_type=r_info&0xffffffff
                sym_index=r_info>>32
                # 1027 = R_AARCH64_RELATIVE, where addend is load RVA.
                if relocation_type in (1027,1025,1026) and sym_index==0:
                    relocs.append({
                        'targetName':name,'targetRva':f'0x{val:X}',
                        'relocationType':relocation_type,
                        'rOffset':f'0x{r_off:X}',
                        'rInfo':f'0x{r_info:X}',
                        'elfAddendFileOffset':f'0x{k:X}',
                        'publishedVtableSlot':(
                            (r_off-vtable_base)//8
                            if r_off>=vtable_base and (r_off-vtable_base)%8==0
                            and r_off<vtable_base+321*8 else None
                        ),
                    })
            start=k+8
    (out/'shiny-wrapper-relocations.json').write_text(
        json.dumps({'targetRelocations':relocs,'note':'Confirmed relocation entries only; callers require vtable dispatch analysis'},
                   ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'shiny-wrapper-pointer-map.json').write_text(
        json.dumps({'matches':pointer_hits,'publishedPokemonParamVtable':vtable_summary,
                    'warning':'function pointer in data is not proof of dynamic shiny or rare invocation'},
                   ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    schema=fields(root)
    if not schema:raise ValueError('No rare named field in actual BFBS')
    info={'version':'2.0.2','buildId':m['modules']['main']['buildIdHex'],
          'elfSha256':digest,'textStartRva':f'0x{textva:X}', 'textEndRva':f'0x{end:X}',
          'textBytes':len(code),'schemaRareFields':schema,
          'directBlCounts':{name:len(reverse[target]) for name,target in FUNCTIONS.items()},
          'highBit28to31TBZCandidates':len(msb_tests),
          'directTailBranchCounts':{name:len(tails[target]) for name,target in FUNCTIONS.items()},
          'highNibbleExtractCandidates':len(shifts),'exportedCandidates':min(500,len(shifts)),
          'exactWordHitsInCode':{f'0x{word:X}':[f'0x{x:X}' for x in sites[:30]] for word,sites in literal.items()},
          'externalFunctionReferencesOnly':'https://decryptu.github.io/pokeldn/za.html',
          'result':'Independent ELF static scan. No Encounter.rare to PID path proven.',
          'runtimeConfirmed':False,'shinyLockBranchRva':None,
          'next':'Trace candidate at matching Build ID. Prove encounter rare input and first 1/2/3 branch; follow PID/TID/SID and final shiny outcome.'}
    (out/'static-audit.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    mdlines=['# ZA v2.0.2 ELF ARM64 只读扫描结果','',
       '> 这些是实际 AArch64 指令、BFBS 字段和直接 BL 交叉引用，但不是已经定位的锁闪分支。','',
       f'- Build ID：{info["buildId"]}', f'- SHA-256：{digest}',
       f'- .text：main+0x{textva:X} 到 main+0x{end:X}；{len(code):,} bytes',
       f'- UBFM/LSR 高 4 位提取候选：{len(shifts)}', '',
       '## 真实 BFBS rare 字段', '']
    mdlines += [f'- {x["object"]}.{x["name"]}：field ID {x["fieldId"]}，'
                f'vtable slot offset {x["vtableSlotByteOffset"]}；该值不是运行时地址。'
                for x in schema]
    mdlines += ['', '## 公开 Getter/Setter 的直接 BL 计数','',
                '| 入口 RVA | 直接 BL 次数 |','|---|---:|']
    mdlines += [f'| {name} main+0x{target:X} | {len(reverse[target])} |'
                for name,target in FUNCTIONS.items()]
    mdlines += ['', '## RELA 虚函数指针重定位','',
                f'- 符合 AArch64 RELATIVE relocation 的目标地址记录：{len(relocs)}。',
                '- 详情 shiny-wrapper-relocations.json；这只是 vtable 的位置证据。','']
    mdlines += ['', '## 虚函数包装器的 ELF 指针交叉引用','',
                f'- 找到 {len(pointer_hits)} 处与目标包装器/函数 RVA 相同的 64-bit 字面指针。',
                '- 详细位置：shiny-function-pointer-xrefs.csv 与 shiny-wrapper-pointer-map.json。',
                '- 这些不能取代运行时追踪，仍需验证上层间接 BLR 的来源。','']
    mdlines += ['', '## ARM64 B 尾调用与高位测试','',
                f'- 直接 B 尾调用 PID_Set：{len(tails[FUNCTIONS["PID_Set"]])} 个。',
                f'- TBZ/TBNZ 检查 28–31 高位：{len(msb_tests)} 处。',
                '- 已导出 pid-tail-branches.csv、rare-highbit-tests.csv 与 pid-shiny-function-windows.md。',
                '']
    mdlines += ['', '## 优先进一步人工核对的高位候选','',
                '| 指令 RVA | 分数（启发式） | 最近 PID Set BL 距离 |','|---|---:|---:|']
    mdlines += [f'| main+0x{pc:X} | {score} | {dist} |'
                for score,dist,pc,_,_ in candidates[:20]]
    mdlines += ['','## 不可跳过的证据门槛','',
        '1. 在正确 Build ID 的运行实例里证明某处寄存器值确实来自 Encounter.rare。',
        '2. 对 0x1FFFFFFF、0x2FFFFFFF、0x3FFFFFFF 复测该函数第一处分歧分支。',
        '3. 从该分支追踪真实 PID Setter、TID/SID、最终异色 XOR 和重抽路径。',
        '4. 把完整调用栈、汇编、寄存器、实例类型与反例保留为可核查日志。',
        '', '同目录有 pid-direct-callers.csv、shift28-candidates.csv、static-audit.json。',
        '无动态 trace 之前，shinyLockBranchRva 仍为 null。','']
    (out/'README.md').write_text('\n'.join(mdlines),encoding='utf8')
    print(json.dumps({'success':True,'pidSetXrefs':len(pidcalls),
                      'shift28Candidates':len(shifts),'rareFields':schema},ensure_ascii=False))

if __name__=='__main__':main()
