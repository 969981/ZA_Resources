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
             'Species_Get': 0xE49940, 'IV_Get_HP': 0xE4BCF0, 'Personal_Load': 0xE380C0}

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
    textva,code=section((root/ELF).read_bytes())
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
    reverse={v:[] for v in FUNCTIONS.values()};shifts=[];literal={v:[] for v in (0x1FFFFFFF,0x2FFFFFFF,0x3FFFFFFF)}
    for i,(w,) in enumerate(struct.iter_unpack('<I',code)):
        pc=textva+i*4
        if w&0xFC000000==0x94000000:
            imm=w&0x03FFFFFF
            if imm&(1<<25):imm-=1<<26
            target=pc+imm*4
            if target in reverse:reverse[target].append(pc)
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
    schema=fields(root)
    if not schema:raise ValueError('No rare named field in actual BFBS')
    info={'version':'2.0.2','buildId':m['modules']['main']['buildIdHex'],
          'elfSha256':digest,'textStartRva':f'0x{textva:X}', 'textEndRva':f'0x{end:X}',
          'textBytes':len(code),'schemaRareFields':schema,
          'directBlCounts':{name:len(reverse[target]) for name,target in FUNCTIONS.items()},
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
