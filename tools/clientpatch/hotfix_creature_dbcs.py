#!/usr/bin/env python3
"""Hotfix builder for the four creature DBCs in mod-worgoblin's custom layer.

mod-worgoblin's pre-patched Creature*.dbc files were authored against a
vanilla 3.3.5a baseline and ship MODIFIED copies of nearly every stock row
(CreatureDisplayInfo: 7977 row overrides; CreatureDisplayInfoExtra: 15452;
CreatureModelData: 1308). When we use them as the base layer for the
client patch, those overrides silently overwrite the Black Rose realm's
authoritative client DBCs (Patch-F.MPQ / Patch-C.MPQ) - which is what's
been causing mounts and mobs (Spotted Hippogryph, Writhing Haunt, Red
Riding Kodo, Felreaver feet, Helboar, ...) to render with missing /
wrong textures and corrupted outer geosets.

This script rebuilds each affected DBC as (authoritative base) + (only
the net-new rows mod-worgoblin actually added), so we keep the Worgen /
Goblin / new-mount displays without trampling anything else.

Run with no arguments. Reads:
  /tmp/auth-dbc/CreatureDisplayInfo.dbc          (from Patch-F.MPQ)
  /tmp/auth-dbc/CreatureDisplayInfoExtra.dbc     (from Patch-C.MPQ)
  /tmp/auth-dbc/CreatureModelData.dbc            (from Patch-F.MPQ)
  tools/clientpatch/input/custom/DBFilesClient/Creature*.dbc

Writes the hotfix outputs back over the input/custom/ copies.
"""

from __future__ import annotations

import struct
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
CUSTOM_DIR = HERE / "input" / "custom" / "DBFilesClient"
AUTH_DIR = Path("/tmp/auth-dbc")


# Races mod-worgoblin owns on this realm. The vanilla 3.3.5a client ships
# CharSections/CharHairGeosets rows for these race IDs too - race 9 for NPC
# goblin variants and race 12 for Blizzard's FelOrc/early-Worgen NPC textures -
# and those collide with mod-worgoblin's playable-race rows (race lookup is
# (Race, Sex, Type, Var); the first matching row wins, so the authoritative
# rows would intercept and the playable character would render with FelOrc
# faces / NPC goblin hair sections). For these two DBCs only, we drop the
# authoritative rows for the takeover-race set and let mod-worgoblin own
# every (race=9 / race=12) row outright.
PLAYABLE_RACE_TAKEOVER = frozenset({9, 12})


@dataclass
class DbcSpec:
    filename: str
    auth_basename: str
    string_columns: list[int]  # 0-indexed column positions that hold string offsets
    expected_field_count: int
    expected_record_size: int
    # If set, the column index (0-based) that holds the Race ID. When non-None
    # AND the race value is in `PLAYABLE_RACE_TAKEOVER`, the authoritative row
    # is discarded and mod-worgoblin's version is taken instead (regardless of
    # whether the IDs collide).
    race_column: int | None = None


# 3.3.5a (build 12340) layouts. Column positions are 0-indexed; only the
# fields below are string references - everything else is an int or float.
SPECS = [
    DbcSpec(
        filename="CreatureDisplayInfo.dbc",
        auth_basename="CreatureDisplayInfo.dbc",
        string_columns=[6, 7, 8, 9],  # TextureVariation 1/2/3 + PortraitTextureName
        expected_field_count=16,
        expected_record_size=64,
    ),
    DbcSpec(
        filename="CreatureDisplayInfoExtra.dbc",
        auth_basename="CreatureDisplayInfoExtra.dbc",
        string_columns=[20],  # BakedTextureName
        expected_field_count=21,
        expected_record_size=84,
    ),
    DbcSpec(
        filename="CreatureModelData.dbc",
        auth_basename="CreatureModelData.dbc",
        string_columns=[2],  # ModelName
        expected_field_count=28,
        expected_record_size=112,
    ),
    DbcSpec(
        filename="CharSections.dbc",
        auth_basename="CharSections.dbc",
        # 3.3.5a layout (10 uint32s = 40 bytes):
        #   0: ID, 1: RaceID, 2: SexID, 3: BaseSection,
        #   4: TextureName_0, 5: TextureName_1, 6: TextureName_2  (strings)
        #   7: Flags, 8: VariationIndex, 9: ColorIndex
        # An earlier version of this spec listed [5, 6, 7], which left the
        # actual TextureName_0 offset un-repooled and rendered Worgen faces
        # as random texture data (pig snouts).
        string_columns=[4, 5, 6],
        expected_field_count=10,
        expected_record_size=40,
        race_column=1,
    ),
    DbcSpec(
        filename="CharHairGeosets.dbc",
        auth_basename="CharHairGeosets.dbc",
        # 3.3.5a layout (6 uint32s = 24 bytes):
        #   0: ID, 1: RaceID, 2: SexID, 3: VariationID, 4: GeosetID, 5: ShowScalp
        string_columns=[],
        expected_field_count=6,
        expected_record_size=24,
        race_column=1,
    ),
]


def read_dbc(path: Path) -> tuple[int, int, int, bytes, bytes]:
    """Returns (record_count, field_count, record_size, body_bytes, string_pool_bytes)."""
    data = path.read_bytes()
    if data[:4] != b"WDBC":
        sys.exit(f"{path}: not a WDBC file")
    recs, fields, rec_size, sblock = struct.unpack("<IIII", data[4:20])
    body = data[20 : 20 + recs * rec_size]
    string_pool = data[20 + recs * rec_size : 20 + recs * rec_size + sblock]
    if len(body) != recs * rec_size:
        sys.exit(f"{path}: truncated body")
    if len(string_pool) != sblock:
        sys.exit(f"{path}: truncated string pool")
    return recs, fields, rec_size, body, string_pool


def read_cstring_at(pool: bytes, offset: int) -> bytes:
    if offset >= len(pool):
        return b""
    end = pool.index(b"\x00", offset)
    return pool[offset:end]


def write_dbc(path: Path, field_count: int, rec_size: int, body: bytes, string_pool: bytes) -> None:
    assert len(body) % rec_size == 0, "body not aligned to record size"
    rec_count = len(body) // rec_size
    header = struct.pack(
        "<4sIIII", b"WDBC", rec_count, field_count, rec_size, len(string_pool)
    )
    path.write_bytes(header + body + string_pool)


def hotfix_one(spec: DbcSpec) -> None:
    auth_path = AUTH_DIR / spec.auth_basename
    cust_path = CUSTOM_DIR / spec.filename
    if not auth_path.exists():
        sys.exit(f"missing authoritative: {auth_path}")
    if not cust_path.exists():
        sys.exit(f"missing custom: {cust_path}")

    a_recs, a_fields, a_rsz, a_body, a_pool = read_dbc(auth_path)
    c_recs, c_fields, c_rsz, c_body, c_pool = read_dbc(cust_path)

    if a_fields != spec.expected_field_count or a_rsz != spec.expected_record_size:
        sys.exit(
            f"{spec.filename}: unexpected layout in authoritative "
            f"(fields={a_fields} expected={spec.expected_field_count}, "
            f"rec_size={a_rsz} expected={spec.expected_record_size})"
        )
    if c_fields != spec.expected_field_count or c_rsz != spec.expected_record_size:
        sys.exit(
            f"{spec.filename}: unexpected layout in custom "
            f"(fields={c_fields}, rec_size={c_rsz})"
        )

    # Step 1: build the authoritative base, dropping any rows whose Race ID
    # is in the playable-race takeover set (so mod-worgoblin's playable
    # Worgen/Goblin rows don't get intercepted by the Patch-C NPC variants
    # that share the race slot).
    a_ids: set[int] = set()
    auth_kept: list[bytes] = []
    auth_dropped_takeover = 0
    for i in range(a_recs):
        rec = a_body[i * a_rsz : (i + 1) * a_rsz]
        rid = struct.unpack("<I", rec[:4])[0]
        if spec.race_column is not None:
            race_off = spec.race_column * 4
            race = struct.unpack("<I", rec[race_off : race_off + 4])[0]
            if race in PLAYABLE_RACE_TAKEOVER:
                auth_dropped_takeover += 1
                continue
        a_ids.add(rid)
        auth_kept.append(rec)

    # Step 2: walk every mod-worgoblin row. Keep it if either
    #   - its ID is not already in the (post-takeover) authoritative base, or
    #   - its Race is in the playable-race takeover set (mod-worgoblin owns
    #     these regardless of ID collisions).
    new_pool = bytearray(a_pool)
    appended_string_cache: dict[bytes, int] = {}
    net_new_records: list[bytes] = []
    overrides_dropped = 0
    race_takeovers_added = 0

    for i in range(c_recs):
        rec_bytes = bytearray(c_body[i * c_rsz : (i + 1) * c_rsz])
        rid = struct.unpack("<I", rec_bytes[:4])[0]

        is_race_takeover = False
        if spec.race_column is not None:
            race_off = spec.race_column * 4
            race = struct.unpack("<I", rec_bytes[race_off : race_off + 4])[0]
            is_race_takeover = race in PLAYABLE_RACE_TAKEOVER

        if not is_race_takeover and rid in a_ids:
            overrides_dropped += 1
            continue

        # Re-pool any string offsets so they reference new_pool (the
        # authoritative file's string block extended) instead of the custom
        # file's own pool.
        for col_idx in spec.string_columns:
            off_pos = col_idx * 4
            old_off = struct.unpack("<I", rec_bytes[off_pos : off_pos + 4])[0]
            if old_off == 0:
                continue
            s_bytes = read_cstring_at(c_pool, old_off)
            if not s_bytes:
                # offset pointed at empty string; safe to remap to pool[0]
                struct.pack_into("<I", rec_bytes, off_pos, 0)
                continue
            cached = appended_string_cache.get(s_bytes)
            if cached is not None:
                struct.pack_into("<I", rec_bytes, off_pos, cached)
            else:
                new_off = len(new_pool)
                new_pool.extend(s_bytes + b"\x00")
                appended_string_cache[s_bytes] = new_off
                struct.pack_into("<I", rec_bytes, off_pos, new_off)
        net_new_records.append(bytes(rec_bytes))
        if is_race_takeover:
            race_takeovers_added += 1

    out_body = b"".join(auth_kept) + b"".join(net_new_records)
    write_dbc(cust_path, a_fields, a_rsz, out_body, bytes(new_pool))

    takeover_str = ""
    if spec.race_column is not None and (
        auth_dropped_takeover or race_takeovers_added
    ):
        takeover_str = (
            f"  [race-takeover: -{auth_dropped_takeover} auth, "
            f"+{race_takeovers_added} custom]"
        )
    print(
        f"  {spec.filename:32}  base rows={len(auth_kept):6d}  "
        f"+net-new={len(net_new_records):4d}  "
        f"overrides dropped={overrides_dropped:5d}  "
        f"-> total={len(auth_kept) + len(net_new_records):6d}{takeover_str}"
    )


def main() -> int:
    print("Black Rose | hotfix: rebuild mod-worgoblin creature DBCs from authoritative bases")
    print()
    for spec in SPECS:
        hotfix_one(spec)
    print()
    print("Done. The mod-worgoblin creature DBC overrides have been replaced with")
    print("(Patch-F.MPQ / Patch-C.MPQ authoritative base) + (only the net-new mod-worgoblin rows).")
    print("Re-run `python3 build_patch.py merge` and repack Patch-Z.MPQ to ship the fix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
