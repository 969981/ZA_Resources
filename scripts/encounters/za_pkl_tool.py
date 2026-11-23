#!/usr/bin/env python3
"""Pack and validate Z-A wild encounter PKL from pkNX slot_sets JSON (stdlib only).

Inputs are the t1_slot_sets.json, t2_slot_sets.json and t3_slot_sets.json
exported by pkNX SpawnExporter. Hyperspace has its own upstream exporter;
this tool supports inspecting it, but does not synthesize its data.
"""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import re
import struct

LOCATION = re.compile(r"\((\d+)\)\s*$")
ENC = struct.Struct('<HBBBBBB')


class PKLError(ValueError):
    pass


def read_sets(paths):
    areas = defaultdict(list)
    provenance = []
    for path in paths:
        path = Path(path)
        data = path.read_bytes()
        provenance.append({'file': str(path), 'sha256': hashlib.sha256(data).hexdigest()})
        document = json.loads(data)
        if not isinstance(document, dict):
            raise PKLError(f'{path}: expected object: location name -> slot array')
        for name, slots in document.items():
            match = LOCATION.search(name)
            if not match:
                raise PKLError(f'{path}: no location ID suffix in {name!r}')
            loc = int(match.group(1))
            if not 0 < loc <= 65535:
                raise PKLError(f'{path}: invalid location {loc}')
            if not isinstance(slots, list):
                raise PKLError(f'{path}: expected array for location {loc}')
            for item in slots:
                areas[loc].append(encode_slot(item, path, loc))
    if not areas:
        raise PKLError('No encounter areas found')
    return areas, provenance


def encode_slot(o, source, loc):
    try:
        species = int(o['Species'])
        form = int(o['Form'])
        gender = int(o['Gender'])
        level_min = int(o['LevelMin'])
        level_max = int(o['LevelMax'])
        alpha = o['IsAlpha']
        shiny = o['Shiny']
        nature = int(o['Nature'])
    except (KeyError, TypeError, ValueError) as ex:
        raise PKLError(f'{source}:{loc}: invalid slot {o!r}: {ex}') from ex
    if not isinstance(alpha, bool):
        raise PKLError(f'{source}:{loc}: IsAlpha must be true/false')
    if nature != -1:
        raise PKLError(f'{source}:{loc}: fixed nature={nature}; use static encounter model')
    if not (1 <= species <= 65535 and 0 <= form <= 255):
        raise PKLError(f'{source}:{loc}: species or form out of range: {species}, {form}')
    if gender not in (-1, 0, 1, 2):
        raise PKLError(f'{source}:{loc}: unsupported gender {gender}')
    if not 1 <= level_min <= level_max <= 100:
        raise PKLError(f'{source}:{loc}: invalid level range {level_min}-{level_max}')
    # pkNX Shiny enum: Random=0, Always=1, Never=2.
    # PKL Shiny: Random=0, Never=1, Always=2.
    if isinstance(shiny, str):
        codes = {'Random': 0, 'Always': 2, 'Never': 1}
        if shiny not in codes:
            raise PKLError(f'{source}:{loc}: unknown Shiny name {shiny!r}')
        code = codes[shiny]
    elif type(shiny) is int and shiny in (0, 1, 2):
        code = {0: 0, 1: 2, 2: 1}[shiny]
    else:
        raise PKLError(f'{source}:{loc}: unknown Shiny {shiny!r}')
    return species, form, gender & 0xff, level_min, level_max, int(alpha), code


def condense(slots):
    """Like pkNX: coalesce overlapping level ranges for equal non-level fields.
    Do not coalesce merely adjacent ranges.
    """
    by_key = defaultdict(list)
    for s in slots:
        by_key[(s[0], s[1], s[2], s[5], s[6])].append((s[3], s[4]))
    result = []
    for (species, form, gender, alpha, shiny), ranges in sorted(by_key.items()):
        ranges.sort()
        merged = []
        for low, high in ranges:
            if merged and low <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(high, merged[-1][1]))
            else:
                merged.append((low, high))
        result += [(species, form, gender, low, high, alpha, shiny) for low, high in merged]
    return result


def pack(areas):
    blocks = []
    for loc in sorted(areas):
        slots = condense(areas[loc])
        if not slots:
            continue
        blocks.append((loc, struct.pack('<HH', loc, 0) + b''.join(ENC.pack(*x) for x in slots)))
    if not blocks:
        raise PKLError('All locations have zero encounters')
    if len(blocks) > 65535:
        raise PKLError('Too many locations for BinLinker16')
    count = len(blocks)
    first = 4 + 2 * (count + 1)
    offsets = [first]
    body = bytearray()
    for _, block in blocks:
        body.extend(block)
        while (first + len(body)) % 2:
            body.append(0)
        end = first + len(body)
        if end > 65535:
            raise PKLError('BinLinker16 offset overflow; cannot write PKHeX-compatible PKL')
        offsets.append(end)
    return b'za' + struct.pack('<H', count) + struct.pack('<' + 'H' * len(offsets), *offsets) + body


def inspect(data):
    if len(data) < 8 or data[:2] != b'za':
        raise PKLError('Not a ZA BinLinker16 encounter file')
    n = struct.unpack_from('<H', data, 2)[0]
    start = 4 + 2 * (n + 1)
    if len(data) < start:
        raise PKLError('Truncated BinLinker offsets')
    offsets = struct.unpack_from('<' + 'H' * (n + 1), data, 4)
    if n == 0 or offsets[0] != start or offsets[-1] != len(data) or list(offsets) != sorted(offsets):
        raise PKLError('Invalid BinLinker offsets or end marker')
    counts, records = {}, []
    for i in range(n):
        a, b = offsets[i], offsets[i+1]
        if b - a < 4 or (b - a - 4) % ENC.size:
            raise PKLError(f'Area {i} has invalid length {b-a}')
        loc, reserved = struct.unpack_from('<HH', data, a)
        if reserved != 0 or loc in counts:
            raise PKLError(f'Area {i} has invalid reserved field or duplicate location {loc}')
        counts[loc] = (b - a - 4) // ENC.size
        for pos in range(a+4, b, ENC.size):
            rec = ENC.unpack_from(data, pos)
            if rec[0] == 0 or rec[3] > rec[4] or rec[5] not in (0, 1) or rec[6] not in (0, 1, 2):
                raise PKLError(f'Area {loc}, offset {pos}: invalid encounter record')
            records.append((loc,) + rec)
    return {'area_count': n, 'slot_count': len(records), 'location_slots': {str(k): v for k,v in sorted(counts.items())},
            'alpha_slots': sum(x[6] == 1 for x in records),
            'shiny_never_slots': sum(x[7] == 1 for x in records),
            'shiny_always_slots': sum(x[7] == 2 for x in records)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--build', nargs='+', metavar='SLOT_SETS_JSON', help='Build encounter_za.pkl from pkNX t1/t2/t3_slot_sets.json')
    group.add_argument('--inspect', type=Path, metavar='PKL', help='Verify and summarize existing ZA encounter PKL')
    ap.add_argument('--out', type=Path, default=Path('encounter_za.pkl'))
    args = ap.parse_args()
    if args.inspect:
        data = args.inspect.read_bytes()
        result = inspect(data)
        result.update(file=str(args.inspect), sha256=hashlib.sha256(data).hexdigest())
    else:
        areas, sources = read_sets(args.build)
        data = pack(areas)
        result = inspect(data)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
        result.update(file=str(args.out), sha256=hashlib.sha256(data).hexdigest(), sources=sources)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (PKLError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f'Error: {exc}')
