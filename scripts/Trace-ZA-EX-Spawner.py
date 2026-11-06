#!/usr/bin/env python3
"""Read-only crosswalk from ZA event battle actor IDs to PokemonSpawnerData and EncountData.

All fields explicitly use current pkNX PokemonSpawnerDataDBArray.fbs order.
Records not found remain UNKNOWN; no prefix-join heuristic counts as proof.
"""
import argparse, hashlib, json, struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"Unpack/v2.0.2/romfs/arc/data.trpfs/virtual/world/ik_data/field/pokemon_spawner/pokemon_spawner_data/pokemon_spawner_data_array.bin"
OUTPUT=ROOT/"docs/research/v2.0.2/za-ex1-ex2-spawner-crosswalk.json"
TARGET_SPAWNERS={"id_sub119_01","id_sub120_01"}
TARGET_ENCOUNTERS={"sub_119_diancie","sub_120_mewtwo"}

class Flat:
    def __init__(self,raw):
        self.raw=raw
    def valid(self,pos,n=4):
        return 0<=pos<=len(self.raw) and 0<=n<=len(self.raw)-pos
    def u32(self,pos):
        if not self.valid(pos): raise ValueError("u32 outside file")
        return struct.unpack_from("<I",self.raw,pos)[0]
    def i32(self,pos):
        if not self.valid(pos): raise ValueError("i32 outside file")
        return struct.unpack_from("<i",self.raw,pos)[0]
    def u16(self,pos):
        if not self.valid(pos,2): raise ValueError("u16 outside file")
        return struct.unpack_from("<H",self.raw,pos)[0]
    def ptr(self,pos):
        if pos is None:return None
        dest=pos+self.u32(pos)
        if not self.valid(dest):raise ValueError("invalid relative pointer")
        return dest
    def field(self,tab,index):
        vt=tab-self.i32(tab)
        n=self.u16(vt)
        if n<4 or n>512:raise ValueError("bad vtable")
        if 4+2*index>=n:return None
        offset=self.u16(vt+4+2*index)
        if not offset:return None
        at=tab+offset
        if not self.valid(at):raise ValueError("bad table field")
        return at
    def str(self,pos):
        if pos is None:return None
        where=self.ptr(pos)
        length=self.u32(where)
        if length>100000 or not self.valid(where+4,length):
            raise ValueError("bad string size")
        return self.raw[where+4:where+4+length].decode("utf-8","replace")
    def array(self,tab,index):
        where=self.ptr(self.field(tab,index))
        if where is None:return []
        length=self.u32(where)
        if length>50000 or not self.valid(where+4,length*4):
            raise ValueError("bad vector bounds")
        return [self.ptr(where+4+4*i) for i in range(length)]
    def num(self,tab,index):
        pos=self.field(tab,index)
        return 0 if pos is None else self.i32(pos)
    def sval(self,tab,index):
        return self.str(self.field(tab,index))

def extract(raw):
    fb=Flat(raw)
    root=fb.u32(0)
    dbs=fb.array(root,0)
    rows=0
    selected=[]
    hits_by_spawner=[]
    hits_by_encounter=[]
    all_ids=[]
    for di,db in enumerate(dbs):
        for ri,spawner in enumerate(fb.array(db,0)):
            rows+=1
            sid=fb.sval(spawner,0)
            all_ids.append(sid)
            encs=[]
            for ei,enc in enumerate(fb.array(spawner,5)):
                encs.append({
                    "enc_index":ei,
                    "encounter_id":fb.sval(enc,0),
                    "weight":fb.num(enc,1),
                    "max_count":fb.num(enc,2),
                    "additional_level":fb.num(enc,3)
                })
            matched_spawner=sid in TARGET_SPAWNERS
            matched_encounter=any(e["encounter_id"] in TARGET_ENCOUNTERS for e in encs)
            if not (matched_spawner or matched_encounter):continue
            objects=[]
            for oi,obj in enumerate(fb.array(spawner,1)[:16]):
                objects.append({
                    "object_index":oi,
                    "object_name":fb.sval(obj,0),
                    "scene":fb.sval(obj,1),
                    "battle_area_id":fb.sval(obj,4),
                })
            row={"db_index":di,"row_index":ri,"spawner_id":sid,
                 "spawner_table_offset":"0x%X"%spawner,
                 "encounters":encs, "appearance_objects":objects,
                 "match_spawner_id":matched_spawner, "match_encounter_id":matched_encounter}
            selected.append(row)
            if matched_spawner:hits_by_spawner.append(row)
            if matched_encounter:hits_by_encounter.append(row)
    def exact(sid,enc):
        return [
            {"spawner_id":x["spawner_id"],"db_index":x["db_index"],"row_index":x["row_index"],
             "enc_index":z["enc_index"],"encounter_id":z["encounter_id"]}
            for x in selected if x["spawner_id"]==sid
            for z in x["encounters"] if z["encounter_id"]==enc]
    return {"database_count":len(dbs),"spawner_count":rows,
            "matched_rows":selected,
            "target_id_literal_presence":{s:s.encode() in raw for s in sorted(TARGET_SPAWNERS|TARGET_ENCOUNTERS)},
            "target_spawner_record_count":len(hits_by_spawner),
            "target_encounter_record_count":len(hits_by_encounter),
            "verified_exact_joins":{
                "diancie":exact("id_sub119_01","sub_119_diancie"),
                "mewtwo":exact("id_sub120_01","sub_120_mewtwo"),
            },
            "warning":"A record ID match is static FlatBuffers linkage, not proven runtime execution, battle dispatch, or shiny branch."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=SOURCE)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args()
    data=args.source.read_bytes()
    result=extract(data)
    result.update({"game_version":"ZA 2.0.2","source_path":str(args.source),
                   "source_size":len(data),"source_sha256":hashlib.sha256(data).hexdigest()})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"source_sha256":result["source_sha256"],
                      "database_count":result["database_count"],"spawner_count":result["spawner_count"],
                      "target_id_presence":result["target_id_literal_presence"],
                      "exact_joins":result["verified_exact_joins"],"matched_count":len(result["matched_rows"])},indent=2))
if __name__=="__main__":
    main()
