#!/usr/bin/env python3
"""Publish ZA v2.0.2 audited CSVs into category folders, with browseable previews."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

DEST = Path("Unpack/v2.0.2/romfs/arc/data.trpfs/virtual_converted/_tables")
GROUPS = {
    "encounters": ["ZA_encounters_flat.csv", "ZA_spawner_encounter_join.csv",
                   "encounter.records.csv", "spawner.records.csv", "pokemon.records.csv"],
    "maps": ["ZA_spawn_points.csv", "ZA_zones.csv", "spawn_transform.records.csv",
             "wild_zone.records.csv", "field_wild_zone.records.csv",
             "field_location.records.csv", "field_scene_area.records.csv",
             "area_jump.records.csv"],
    "trainers": ["ZA_trainer_parties.csv", "trainer.records.csv", "trainer_env.records.csv"],
    "items": ["ZA_item_lottery.csv", "EXL_items_raw.csv", "EXL_shops_raw.csv",
              "pokemon_drop.records.csv", "item_ball.records.csv",
              "item_ball_spawner.records.csv", "item_type.records.csv"],
    "pokedex": ["EXL_pokedex_raw.csv", "EXL_dex_distribution_raw.csv"],
    "battle": ["waza_attribute.records.csv", "oyabun_waza.records.csv",
               "oyabun_setting.records.csv", "battle_setting.records.csv",
               "capture.records.csv"],
    "_audit": ["manifest.csv"],
}
LABELS = {
    "encounters": "遭遇、生成器与宝可梦场景配置",
    "maps": "地图、区域和出生位置",
    "trainers": "训练家及队伍",
    "items": "道具、商店与掉落",
    "pokedex": "图鉴（无 Schema 原始字段）",
    "battle": "招式属性、头目和战斗参数",
    "_audit": "数据来源和核验清单",
}
AUDIT_JSON = ["manifest.json", "ZA_relation_summary.json", "EXL_raw_summary.json"]

def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            h.update(block)
    return h.hexdigest()

def copy_csv(src, dst, preview_n):
    dst.parent.mkdir(parents=True, exist_ok=True)
    csv.field_size_limit(64 * 1024 * 1024)
    with src.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)
        if not header:
            raise ValueError(f"Missing header: {src}")
        count = 0
        sample = []
        for line in reader:
            count += 1
            if len(line) != len(header):
                raise ValueError(f"Column mismatch in {src} at row {count + 1}")
            if count <= preview_n:
                sample.append(line)
    shutil.copyfile(src, dst)
    if count > preview_n:
        with dst.with_name(dst.stem + ".preview.csv").open(
            "w", newline="", encoding="utf-8-sig"
        ) as output:
            w = csv.writer(output)
            w.writerow(header)
            w.writerows(sample)
    return {"rows": count, "bytes": dst.stat().st_size, "sha256": sha256(dst),
            "columns": header, "preview": count > preview_n}

def publish(repo, src, preview):
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    joined = json.loads((src / "ZA_relation_summary.json").read_text(encoding="utf-8"))
    exl = json.loads((src / "EXL_raw_summary.json").read_text(encoding="utf-8"))
    if manifest.get("count") != 20 or manifest.get("succeeded") != 20 or manifest.get("failed") != 0:
        raise ValueError("Expected 20/20 successful BFBS decodes")
    if joined.get("allReferencesResolved") is not True:
        raise ValueError("Encounter references not fully joined")
    if len(exl.get("files", {})) != 4 or any(
        item.get("status") != "STRUCTURE_ONLY" for item in exl["files"].values()
    ):
        raise ValueError("Missing or invalid EXL structural probe")
    root = repo / DEST
    report = {"version": "ZA v2.0.2", "evidence": "BFBS decoded; EXL raw STRUCTURE_ONLY", "files": {}}
    lines = [
        "# ZA v2.0.2 — CSV 数据索引", "",
        "从 ROM 的 `virtual/` 提取并转换，生成文件整理在本目录，原文件不修改。",
        "用于 GitHub 网页浏览的大 CSV 提供前 100 行的 `.preview.csv`，完整 CSV 仍然保留。",
        "",
        "> [!IMPORTANT]",
        "> 图鉴和 EXL 道具的原始字段目前**没有 Schema**，只能查看字段槽位，",
        "> **不能根据原始值推断锁闪、固定个体或游戏内部 ID 的真实语义**。",
        "> 部分区域关联是命名推断；遇到无法匹配的坐标不能视为原资源不存在。",
        "",
        "## 按类别查看", "",
    ]
    for group, names in GROUPS.items():
        lines.append(f"### {LABELS[group]} — {group}/")
        lines.append("")
        for name in names:
            from_file = src / name
            if not from_file.is_file():
                raise FileNotFoundError(from_file)
            target = root / group / name
            stat = copy_csv(from_file, target, preview)
            report["files"][f"{group}/{name}"] = stat
            link = f" · [前{preview}行]({group}/{target.stem}.preview.csv)" if stat["preview"] else ""
            lines.append(f"- [{name}]({group}/{name}) — {stat['rows']:,} 行{link}")
        lines.append("")
    root.joinpath("_audit").mkdir(parents=True, exist_ok=True)
    for name in AUDIT_JSON:
        shutil.copyfile(src / name, root / "_audit" / name)
    (root / "_audit" / "published-csv-sha256.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines += [
        "## 原生中文名称、Personal 学习表与 Rare 研究", "",
        "> 下列 13 张扩展 CSV 在本工作流的下一步由 Export-ZA-CoreDex.py 与 "
        "Audit-ZA-Rare.py 追加生成，不属于上面的 31 张 BFBS/EXL 原始 CSV。", "",
        "- [简体中文宝可梦名称](names/ZA_species_names_zh.csv) — 1,026 条",
        "- [简体中文招式名称](names/ZA_move_names_zh.csv) — 921 条",
        "- [简体中文道具名称](names/ZA_item_names_zh.csv) — 2,685 条",
        "- [中文区域标签](names/ZA_place_names_zh.csv) — 284 条",
        "- [原生 Personal 物种/形态](pokedex/ZA_personal_species_forms.csv) — 1,445 条",
        "- [完整原生招式学习表（中文）](battle/ZA_levelup_learnsets_zh.csv) — 20,234 条",
        "- [原生招式主表（威力/命中/PP/属性）](battle/ZA_move_stats_zh.csv) — 902 条",
        "- [原生招式未知字段偏移审计](battle/ZA_move_fields_raw.csv) — 902 条",
        "- [中文招式描述](battle/ZA_move_descriptions_zh.csv)",
        "- [中文图鉴文字 A](pokedex/ZA_pokedex_comment_A_zh.csv) — 1,466 条",
        "- [中文图鉴文字 B](pokedex/ZA_pokedex_comment_B_zh.csv) — 1,412 条",
        "- [全部 Encounter 的 Rare 原始值](encounters/ZA_rare_static_audit.csv) — 1,966 条",
        "- [特别剧情事件 Rare 比较](encounters/ZA_special_event_examples.csv) — 7 条",
        "- [原始文本/Personal 数据 SHA-256](_audit/ZA_core_dex_manifest.json)",
        "- [Rare 字段分布验证](_audit/ZA_rare_static_summary.json)", "",
        "以上中文名称直接来自 ZA v2.0.2 的 Simp_Chinese 消息资源；"
        "Personal 学习向量来自 avalon/data/personal_array.bin，招式主表来自 avalon/data/waza_array.bin。"
        "图鉴 EXL 的业务排序与运行时锁闪仍未验证。", "",
        "- [362+2 个 Personal 可用物种 Obsidian 索引]"
        "(https://github.com/969981/ZA_Resources/blob/"
        "docs/za-v2.0.2-obsidian-extraction/docs/obsidian/ZA-v2.0.2/"
        "22-宝可梦数据档案索引.md)", "",
    ]
    lines += ["## 校验", "",
              f"- BFBS 解码：20/20 成功；失败 0。",
              f"- 生成器→遭遇引用：{joined['spawnerEncounterReferences']:,} 次；未匹配 0。",
              f"- CSV 完整文件：{len(report['files'])} 个（不包括预览 CSV）。",
              "- [关联结果](_audit/ZA_relation_summary.json) · "
              "[转换清单](_audit/manifest.json) · "
              "[CSV SHA-256 清单](_audit/published-csv-sha256.json)",
              "",
              "原始完整 `*.json.gz` 仍在 Actions Artifacts；相关研究文档见 "
              "`docs/obsidian/ZA-v2.0.2/`。", ""]
    (root / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print("Published", len(report["files"]), "full CSV files to", root)
    for group, names in GROUPS.items():
        print(group, len(names))

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--input", type=Path, default=Path(".za-work/za-data"))
    p.add_argument("--preview-rows", type=int, default=100)
    args = p.parse_args()
    publish(args.repo.resolve(), args.input.resolve(), max(1, args.preview_rows))
