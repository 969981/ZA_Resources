#!/usr/bin/env python3
"""Generate species-focused Obsidian notes from actual ZA v2.0.2 CSV exports.

A generated species card is NOT a validated regional/national Pokédex entry.
Do not synthesize names, shiny locks, learnsets, missing IVs, or world locations.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path

DATA = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables")
DOCS = Path("docs/obsidian/ZA-v2.0.2")
IV = ("ivHp", "ivAtk", "ivDef", "ivSpAtk", "ivSpDef", "ivAgi")
MOVES = ("waza1", "waza2", "waza3", "waza4")
BT = chr(96)


def read(path):
    csv.field_size_limit(64 * 1024 * 1024)
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe(v):
    v = str(v) if v not in (None, "") else "—"
    return v.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def q(v):
    return BT + safe(v) + BT


def intv(v, fallback=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return fallback


def skills(raw, names=None):
    names = names or {}
    try:
        x = json.loads(raw or "{}")
    except (json.JSONDecodeError, TypeError):
        return "JSON 解析错误"
    if not isinstance(x, dict):
        return "原始类型不是对象"
    values = []
    for key in MOVES:
        v = x.get(key)
        if isinstance(v, dict):
            v = v.get("wazaId")
        if v not in (None, "", 0):
            num = intv(v)
            label = names.get(num, "")
            values.append(f"{num}({label})" if label else str(num))
    return ", ".join(values) or "未显式配置"


def table(out, cols, body):
    out.append("| " + " | ".join(cols) + " |")
    out.append("| " + " | ".join("---" for _ in cols) + " |")
    if not body:
        out.append("| " + " | ".join("—" for _ in cols) + " |")
    for values in body:
        out.append("| " + " | ".join(safe(v) for v in values) + " |")
    out.append("")


def generate(repo, output):
    data = repo / DATA
    encounter = read(data / "encounters/ZA_encounters_flat.csv")
    joined = read(data / "encounters/ZA_spawner_encounter_join.csv")
    position = read(data / "maps/ZA_spawn_points.csv")
    trainer = read(data / "trainers/ZA_trainer_parties.csv")
    oyabun = read(data / "battle/oyabun_waza.records.csv")
    species_names = {int(r["id"]): r["zhNameOrText"]
                     for r in read(data / "names/ZA_species_names_zh.csv") if r["id"] != ""}
    move_names = {int(r["id"]): r["zhNameOrText"]
                  for r in read(data / "names/ZA_move_names_zh.csv") if r["id"] != ""}
    place_names = {r["label"]: r["zhNameOrText"]
                   for r in read(data / "names/ZA_place_names_zh.csv")}
    zone_key_by_id = {r["zoneID"]: r["placeNameKey"] for r in read(data / "maps/ZA_zones.csv")}
    native_learnsets = read(data / "battle/ZA_levelup_learnsets_zh.csv")
    comments_a = read(data / "pokedex/ZA_pokedex_comment_A_zh.csv")
    comments_b = read(data / "pokedex/ZA_pokedex_comment_B_zh.csv")
    audit = json.loads((data / "_audit/ZA_relation_summary.json").read_text("utf-8"))
    if len(encounter) != audit["encounterRecords"] or not audit["allReferencesResolved"]:
        raise ValueError("Encounter audit or matching incomplete")
    if len(joined) != audit["spawnerEncounterReferences"]:
        raise ValueError("Spawner join count mismatch")
    grouped = collections.defaultdict(lambda: {"enc": [], "spawn": [], "trainer": [], "boss": []})
    learn_by_species = collections.defaultdict(list)
    comments_by_species = collections.defaultdict(list)
    import re
    for row in native_learnsets:
        learn_by_species[row["speciesId"]].append(row)
    for row in comments_a + comments_b:
        match = re.fullmatch(r"ZKN_COMMENT_[AB]_(\d+)_(\d+)", row["label"])
        if match and row["zhNameOrText"].strip():
            comments_by_species[str(int(match.group(1)))].append(row)

    loc = collections.defaultdict(list)
    for r in encounter:
        grouped[r["speciesId"]]["enc"].append(r)
    for r in joined:
        grouped[r["speciesId"]]["spawn"].append(r)
    for r in trainer:
        grouped[r["speciesId"]]["trainer"].append(r)
    for r in position:
        loc[r["spawnerId"]].append(r)
    for r in oyabun:
        o = json.loads(r["row_json"])
        if o.get("devNo") is not None:
            grouped[str(o["devNo"])]["boss"].append(o)
    output.mkdir(parents=True, exist_ok=True)
    ids = sorted({r["speciesId"] for r in encounter}, key=intv)
    index = [
        "---", 'title: "ZA v2.0.2 宝可梦静态资料索引"',
        'zaVersion: "2.0.2"', "category: encounter_species", "---",
        "# 宝可梦静态资料索引（按 devNo）", "",
        "> [!warning] 不是已还原的完整图鉴",
        "> 下列条目从遭遇表的物种 devNo 归纳，不表示正式 Z-A 图鉴成员、"
        "全国图鉴顺序、中文名称或闪光状态已经验证。图鉴 EXL 缺失 schema，"
        "静态配置和运行时实际结果必须区分。", "",
        f"共 {len(ids)} 个不同物种编号、{len(encounter)} 条遭遇、"
        f"{len(joined)} 条生成器引用。每个条目均保留原始 ID 供查证。", "",
        "相关解释：[[12-CSV阅读总指南]] · [[13-遭遇表逐列解读]] · "
        "[[14-生成器刷新与坐标]] · [[21-锁闪与个体字段研究清单]]", "",
    ]
    seen_buckets = set()
    for species in ids:
        rows = grouped[species]
        config, spawners, parties = rows["enc"], rows["spawn"], rows["trainer"]
        min_lv = min(intv(r["minLevel"]) for r in config)
        max_lv = max(intv(r["maxLevel"]) for r in config)
        all31 = sum(all(r.get(k) == "31" for k in IV) for r in config)
        allminus1 = sum(all(r.get(k) == "-1" for k in IV) for r in config)
        fixed_moves = sum(skills(r.get("wazaListJson")) != "未显式配置" for r in config)
        forms = sorted({r["formNo"] for r in config if r["formNo"]}, key=intv)
        zones = sorted({r["zoneIdInferredFromSpawnerName"] for r in spawners
                        if r["zoneIdInferredFromSpawnerName"]})
        file = f"No-{int(species):04d}"
        zh_name = species_names.get(int(species), "")
        native_moves = learn_by_species.get(species, [])
        out = [
            "---", f"speciesId: {int(species)}",
            "speciesNameZh: " + json.dumps(zh_name, ensure_ascii=False),
            'zaVersion: "2.0.2"',
            'dataOrigin: "encounter-devNo"', 'pokedexMembership: "unknown"',
            'shinyLocked: "unknown"', f"encounterConfigCount: {len(config)}",
            f"spawnerReferenceCount: {len(spawners)}",
            f"trainerSlotCount: {len(parties)}", "---",
            f"# {zh_name or '未知名称'} · devNo {species}", "",
            "[[22-宝可梦数据档案索引|返回总索引]] | "
            "[[13-遭遇表逐列解读]] | [[14-生成器刷新与坐标]]", "",
            "> [!warning] 此卡片是数据字典，不是游戏玩法图鉴",
            "> 数据中的物种编号、等级、固定 IV、招式都是源配置；"
            "部分区域仅按名称推断，不等于正式中文出没地点。"
            "rareRaw 不是已确认的锁闪信息。", "",
            "## 静态摘要", "",
            "- 真实简体中文名：" + (zh_name or "本地文本表无对应记录") +
            "（来自 monsname.dat 的 MONSNAME_编号 标签）。",
            f"- 原生 Personal 里的招式学习记录：**{len(native_moves)}** 条"
            "（含形态/特殊学习编码；不能直接当成角色等级）。",
            f"- **遭遇配置** {len(config)}；**生成器引用** {len(spawners)}；"
            f"**训练家队伍槽** {len(parties)}。",
            f"- 跨配置等级包络：**{min_lv}–{max_lv}**；"
            "不是任意同一地点的等级范围。",
            "- 显式形态编号：" + (", ".join(map(q, forms)) if forms else "没有显式非空形态编号") + "。",
            f"- 六项 IV 显式全 31：{all31} 条；六项全 -1：{allminus1} 条。"
            " -1 是原始配置占位候选，不能视为生成个体值。",
            f"- 显式携带预置招式编号的遭遇：{fixed_moves} 条；"
            "未写入不等于学不会。",
            "- 区域编号（从生成器 ID 推断）：" +
            (", ".join(map(q, zones)) if zones else "无；应查看原始 zoneInfo") + "。", "",
            "## 每条遭遇定义", "",
        ]
        enc_rows = []
        for r in config:
            iv = "/".join(r[k] or "∅" for k in IV)
            enc_rows.append([
                q(r["encounterId"]), r["formNo"] or "未显式",
                f'{r["minLevel"]}–{r["maxLevel"]}', iv,
                skills(r["wazaListJson"], move_names), r["rareRaw"] or "未显式",
                r["oyabunProbability"] or "未显式",
            ])
        table(out, ["encounterId", "form", "级别范围", "IV（HP/Atk/Def/Spa/Spd/Spe）",
                    "预置 wazaId", "rareRaw", "头目原值"], enc_rows)
        out += [
            "## 原生 Personal：完整的招式学习向量", "",
            "来自 avalon/data/personal_array.bin 的 FlatBuffers field 25；"
            "moveId、learnLevelRaw、unlockLevelRaw 均直接从 ROM 解码。"
            "253/254 为特殊编码，不是普通等级；present=1 表示此形态可用标志。", "",
        ]
        table(out, ["formNo", "present", "moveId", "招式中文",
                    "学习等级原值", "解锁等级原值", "类别"],
              [[r["formNo"], r["personalPresent"], r["moveId"], r["moveZh"],
                r["learnLevelRaw"], r["unlockLevelRaw"], r["learnCategory"]]
               for r in native_moves])
        out += [
            "## 对应生成器、区域与位置", "",
            "一行表示一条 spawner→encounter 引用；区域来源是名字启发式，"
            "不是全部生成器的源 zoneInfo。坐标为静态 Transform 值。", "",
        ]
        sp_rows = []
        for r in spawners:
            coords = []
            for p in loc.get(r["spawnerId"], []):
                if p.get("matchedTransform") == "1" and all(p.get(k) for k in ("x","y","z")):
                    try:
                        coords.append("(" + ", ".join(f'{float(p[k]):.2f}' for k in ("x","y","z")) + ")")
                    except ValueError:
                        pass
            sp_rows.append([
                q(r["spawnerId"]), q(r["encounterId"]),
                ((r["zoneIdInferredFromSpawnerName"] or "未知") + " / " +
                 place_names.get(zone_key_by_id.get(r["zoneIdInferredFromSpawnerName"], ""), "")
                 if r["zoneIdInferredFromSpawnerName"] else "未知"),
                f'{r["minLevel"]}–{r["maxLevel"]}',
                "; ".join(coords) or "未找到实值",
            ])
        table(out, ["spawnerId", "encounterId", "zone·推断",
                    "等级", "匹配坐标 X/Y/Z"], sp_rows)
        out += [
            "## 训练家队伍中该物种", "",
            "这部分是训练家配置，不代表野生遭遇或可捕获。", "",
        ]
        partyrows = [[q(p["trainerId"]), p["slot"], p["level"] or "未显式",
                      skills(p["movesJson"], move_names), p["rareTypeRaw"] or "未显式"]
                     for p in parties]
        table(out, ["trainerId", "槽位", "等级", "显式 wazaId",
                    "rareTypeRaw"], partyrows)
        out += ["## 头目额外招式原始记录", ""]
        if rows["boss"]:
            for o in rows["boss"]:
                for v in o.get("formTableList", []):
                    out.append("- formNo=" + q(v.get("formNo", "未显式"))
                               + ", wazaNo=" + q(v.get("wazaNo", "未显式")))
        else:
            out.append("头目招式表中没有此物种的显式记录；这不代表不可能成为头目。")
        out += [
            "", "## Z-A 中文图鉴说明的源标签", "",
            "下列文字按 ZKN_COMMENT_A/B_{speciesId}_{suffix} 标签匹配；"
            "后缀不是已验证的图鉴 formNo，不能用它推断正式图鉴排序。", "",
        ]
        if comments_by_species.get(species):
            for row in comments_by_species[species]:
                out.append("- **" + q(row["label"]) + "**：" +
                           safe(row["zhNameOrText"]).replace("\\n", " / "))
        else:
            out.append("现有 zukan_comment_A/B 无对应的非空中文说明。")
        out += [
            "", "## 数据来源与限制", "",
            "- 原始 encounter：world/ik_data/field/pokemon/encount_data/encount_data/encount_data_array.bin",
            "- 原始 spawner：world/ik_data/field/pokemon_spawner/pokemon_spawner_data/pokemon_spawner_data_array.bin",
            "- 原始变换：world/ik_data/field/spawner_transform_data/pokemon_spawner_transform/pokemon_spawner_transform_array.bin",
            "- 物种汉字名称、图鉴正式成员、升级习得招式、技能威力、"
            "最终 IV、PID 和锁闪机制仍需对应 schema/运行时证据。",
            "- 完整数据和哈希：[[18-导出复现与验收]]；"
            "可信度边界：[[20-字段缺省值与证据级别]]。", "",
        ]
        (output / (file + ".md")).write_text("\n".join(out), encoding="utf-8")
        bucket = int(species) // 100
        if bucket not in seen_buckets:
            seen_buckets.add(bucket)
            index += [f"### {bucket*100:04d}–{bucket*100+99:04d}", ""]
        index.append(f"- [[宝可梦档案/{file}|devNo {species}]]"
                     f" · {species_names.get(int(species), '未命名')} · 遭遇 {len(config)}"
                     f" · 生成 {len(spawners)} · 学习 {len(native_moves)} · 队伍槽 {len(parties)}")
    index += ["", "## 数值解释与检索", "",
              "物种编号 devNo 并非已经证明的 Z-A 图鉴内部排序；"
              "EXL 图鉴表的 364 个原始记录仍是 STRUCTURE_ONLY。",
              "想找中文物种名、招式名和真正图鉴顺序，"
              "要继续解码 ik_message 和图鉴表结构，不得凭序号直接补齐。",
              "静态 rareRaw/rareTypeRaw 不是闪光结论。",
              "", "生成器脚本：scripts/Generate-ZA-PokemonObsidian.py", ""]
    (output.parent / "22-宝可梦数据档案索引.md").write_text(
        "\n".join(index), encoding="utf-8")
    print(f"Generated {len(ids)} species notes and main index: {output}")
    return len(ids)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    args = ap.parse_args()
    repo = args.repo.resolve()
    root = repo / DOCS / "宝可梦档案"
    count = generate(repo, root)
    if count != 362:
        raise SystemExit(f"Unexpected species count: {count}")
if __name__ == "__main__":
    main()
