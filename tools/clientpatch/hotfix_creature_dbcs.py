#!/usr/bin/env python3
# ruff: noqa: W605
r"""Hotfix builder for the five creature/character DBCs in mod-worgoblin's
custom layer, plus a post-merge fixup pass for CharSections.dbc that the
3.3.5a client requires.

== Why this exists ==

mod-worgoblin's pre-patched Creature*.dbc and Char*.dbc files were authored
against a vanilla 3.3.5a baseline and ship MODIFIED copies of nearly every
stock row (CreatureDisplayInfo: 7977 row overrides; CreatureDisplayInfoExtra:
15452; CreatureModelData: 1308; CharSections: 2341; CharHairGeosets: 333;
CharacterFacialHairStyles: 220 stock rows with every Geoset[N] zeroed).
When we use them as the base layer for the client patch, those overrides
silently overwrite the Black Rose realm's authoritative client DBCs
(Patch-F.MPQ / Patch-C.MPQ) - which is what was causing mounts and mobs
(Spotted Hippogryph, Writhing Haunt, Red Riding Kodo, Felreaver feet,
Helboar, ...) to render with missing / wrong textures and corrupted outer
geosets, and what was making the Undead Female lower jaw render as a
geometry hole on every face variant (the zeroed Geoset100/200 fields
told the client not to render the lower-face geoset at all).

The main hotfix rebuilds each affected DBC as (authoritative base) + (only
the net-new rows mod-worgoblin actually added), so we keep the Worgen /
Goblin / new-mount displays without trampling anything else.

== CharSections Texture[2] - what it's for, and why we DON'T fill it ==

The Patch-C HD CharSections layer leaves Texture[2] EMPTY on ~3000 rows.
Vanilla 3.3.5a Patch-X.MPQ instead fills it with a placeholder string
(`Character\Human\Male\HumanMaleSkin00_00.blp`) on every Skin / Face /
FacialHair / Underwear row, and with REAL `ScalpUpperHair*.blp` paths on
Hair rows (race-specific - the scalp shader uses T2 to composite the
upper-hair / pony-tail-base layer on top of the head).

An earlier revision of this script ran a blanket "if Texture[2] is empty,
fill it with `HumanMaleSkin00_00.blp`" pass over every row, hoping that
would fix the Undead Female exposed-jaw rendering bug. It did NOT:
  * On Hair rows the placeholder is the wrong file (it's a human skin,
    not a scalp), so for races whose Hair-section T2 was empty in Patch-C
    (Goblin = 432 rows, Worgen = 140, Draenei = 140, Tauren = 100, ...)
    the scalp shader composited a human-male skin patch onto every hairdo
    and the scalp rendered as a corrupted skin smear.
  * On Undead Face rows the placeholder isn't the Scourge jaw-overlay
    texture the undead head shader is asking for, so the undead jaw
    stayed broken anyway.
So we no longer touch Texture[2] in the main pipeline. The revert mode
below cleans up any DBC that had the bad pass applied to it.

== Usage ==

  python3 hotfix_creature_dbcs.py
      Run the full pipeline. Requires /tmp/auth-dbc/ populated with the
      five authoritative DBCs extracted from Patch-F.MPQ and Patch-C.MPQ.

  python3 hotfix_creature_dbcs.py --charsections-revert-jaw-fixup
      Walk the existing input/custom/CharSections.dbc, find every Texture[2]
      offset that points at the `HumanMaleSkin00_00.blp` placeholder, and
      zero it out. Use this to back out the blanket jaw-fill pass without
      needing the authoritative baseline DBCs to be present.

Reads:
  /tmp/auth-dbc/CreatureDisplayInfo.dbc          (from Patch-F.MPQ)
  /tmp/auth-dbc/CreatureDisplayInfoExtra.dbc     (from Patch-C.MPQ)
  /tmp/auth-dbc/CreatureModelData.dbc            (from Patch-F.MPQ)
  /tmp/auth-dbc/CharSections.dbc                 (from Patch-C.MPQ)
  /tmp/auth-dbc/CharHairGeosets.dbc              (from Patch-C.MPQ)
  tools/clientpatch/input/custom/DBFilesClient/Creature*.dbc
  tools/clientpatch/input/custom/DBFilesClient/Char*.dbc

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

# The placeholder texture vanilla 3.3.5a CharSections puts in Texture[2] on
# every Skin/Face/FacialHair/Hair/Underwear row. The 3.3.5a client engine
# requires SOME non-empty value here; the HD Patch-C layer leaves it empty,
# which is what causes the Undead Female jaw to render as broken geometry.
CHARSECTIONS_T2_PLACEHOLDER = b"Character\\Human\\Male\\HumanMaleSkin00_00.blp"


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


# CharacterFacialHairStyles.dbc gets its own merge pass because its row identity
# is the composite key (RaceID, SexID, VariationID) - there's no PK column 0,
# so the generic hotfix_one() logic (which keys on column 0) can't be reused.
CHARFACIALHAIRSTYLES_FIELDS = 8
CHARFACIALHAIRSTYLES_REC_SIZE = 32


# CreatureDisplayInfo column layout (16 cols, 64 bytes) - only the ones we touch:
CDI_COL_ID = 0
CDI_COL_MODELID = 1
CDI_COL_EXTENDED = 3  # ExtendedDisplayInfoID -> CreatureDisplayInfoExtra.ID, 0 = none

# CreatureDisplayInfoExtra column layout (21 cols, 84 bytes):
#  0: ID            (PK)
#  1: DisplayRaceID    -> CharRaces.ID (9 = Goblin, 12 = Worgen on this realm)
#  2: DisplayGenderID  (0 = Male, 1 = Female)
#  3: SkinID           -> CharSections variation index for type 0 / this race+sex
#  4: FaceID           -> CharSections variation index for type 1
#  5: HairStyleID      -> CharSections variation index for type 3
#  6: HairColorID      -> CharSections color index for the hair row
#  7: FacialHairID     -> CharSections variation index for type 2
#  8..18: NPCItemDisplayID[11] (head, shoulders, shirt, cuirass, belt, legs,
#                               boots, wrists, gloves, tabard, cape)
# 19: Flags
# 20: BakedSkinName (string offset; 0 = client bakes a name dynamically)
CDIE_FIELDS = 21
CDIE_REC_SIZE = 84


# Player-race NPC wrappers added by mod-worgoblin. The CreatureDisplayInfo rows
# 29422 (Model 3141 - playable Goblin male) and 29423 (Model 3142 - playable
# Worgen female) ship with ExtendedDisplayInfoID = 0, so NPCs using them render
# as textureless blue silhouettes (the model loads, but the client has no extra
# row telling it which Skin / Face / Hair to bake from CharSections).
#
# === DISABLED - DO NOT RE-ENABLE WITHOUT A REAL FIX ===
#
# The straightforward fix is to append a fresh CreatureDisplayInfoExtra row
# per display with safe Skin/Face/Hair/FacialHair lookups, point the display
# at it, and let the engine bake. This DOES NOT WORK on the 3.3.5a client:
#
#   1. First attempt seeded Hair=17 (mistakenly reading CharSections col 7
#      = Flags as the VariationIndex - col 8 is the actual VariationIndex).
#      Client null-derefed on the CharHairGeosets lookup the moment the NPC
#      entered render distance. CTD.
#   2. Second attempt used Hair=1 (verified to exist in BOTH CharSections
#      and CharHairGeosets). Still CTD - turned out FacialHair=0 missed the
#      CharacterFacialHairStyles lookup (Worgen has no VariationID=0 row
#      for either gender).
#   3. Third attempt used FacialHair=1 (verified to exist in CharSections,
#      CharHairGeosets, AND CharacterFacialHairStyles). STILL CTD.
#
# Conclusion: the vanilla 3.3.5a engine has no working NPC-bake code path
# for (Race=Worgen, Gender=Female) - the combination didn't exist before
# Cataclysm and there's at least one lookup we haven't been able to find
# from DBC tuning alone. mod-worgoblin's authors knew this, which is why
# they shipped both 29422 and 29423 with ExtendedDisplayInfoID = 0.
#
# The pragmatic fix lives in SQL migration 2026_05_29_00 instead: it points
# the affected NPCs (Lorne / Lane Crowley + Crowmane) at vanilla NPC Worgen
# DisplayIDs that wrap Model 44 (Creature\Worgen\Worgen.mdx), whose M2 has
# baked textures and doesn't need an Extra at all.
#
# Leaving the constant empty + the function intact (it'll no-op) so the
# scaffolding is still here if we ever figure out the missing engine
# lookup. If you re-add entries, validate against ALL these tables before
# shipping:
#   * CharSections (Race, Sex, Type=0/1/2/3, VariationIndex=value)
#   * CharHairGeosets (Race, Sex, VariationID=Hair)
#   * CharacterFacialHairStyles (Race, Sex, VariationID=FacialHair)
# And then test in-game with a player standing next to the NPC - schema-
# correct values are necessary but not sufficient.
PLAYER_RACE_NPC_EXTRAS: list[tuple[int, int, int, int, int, int, int, int, int]] = []


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


def hotfix_charfacialhairstyles() -> None:
    """Rebuild CharacterFacialHairStyles.dbc from authoritative Patch-C base
    plus mod-worgoblin's net-new (Worgen / Goblin / NPC-race) rows.

    mod-worgoblin's pre-shipped CharacterFacialHairStyles.dbc zeroes every
    Geoset[N] field on every stock row (220 of them), which makes the client
    refuse to render the lower-face geoset and gives the Undead Female face
    a missing-jaw hole on every variation. Same trampling pattern as the
    Creature*.dbc files - rebuild from auth + net-new only.
    """
    auth_path = AUTH_DIR / "CharacterFacialHairStyles.dbc"
    cust_path = CUSTOM_DIR / "CharacterFacialHairStyles.dbc"
    if not auth_path.exists():
        sys.exit(f"missing authoritative: {auth_path}")
    if not cust_path.exists():
        sys.exit(f"missing custom: {cust_path}")

    a_recs, a_fields, a_rsz, a_body, a_pool = read_dbc(auth_path)
    c_recs, c_fields, c_rsz, c_body, _c_pool = read_dbc(cust_path)
    for label, fields, rsz in (("auth", a_fields, a_rsz), ("custom", c_fields, c_rsz)):
        if fields != CHARFACIALHAIRSTYLES_FIELDS or rsz != CHARFACIALHAIRSTYLES_REC_SIZE:
            sys.exit(
                f"CharacterFacialHairStyles.dbc: unexpected {label} layout "
                f"(fields={fields}, rec_size={rsz})"
            )

    # Auth base: keep every row except Worgen (12) / Goblin (9) - those slots
    # are owned by mod-worgoblin since the NPC-race rows would otherwise
    # intercept the playable-race lookup.
    auth_kept: list[bytes] = []
    auth_dropped_takeover = 0
    for i in range(a_recs):
        rec = a_body[i * a_rsz : (i + 1) * a_rsz]
        race = struct.unpack("<I", rec[:4])[0]
        if race in PLAYABLE_RACE_TAKEOVER:
            auth_dropped_takeover += 1
            continue
        auth_kept.append(rec)

    # Index auth rows by composite (race, sex, var) key so we can detect
    # which custom rows are truly net-new vs trampling overrides.
    auth_keys: set[tuple[int, int, int]] = set()
    for rec in auth_kept:
        auth_keys.add(struct.unpack("<III", rec[:12]))

    # Walk custom rows: keep them only if (a) race is in the takeover set
    # (mod-worgoblin owns Worgen / Goblin outright) or (b) the composite
    # key isn't already in the auth base (truly net-new row).
    net_new_records: list[bytes] = []
    overrides_dropped = 0
    race_takeovers_added = 0
    for i in range(c_recs):
        rec = c_body[i * c_rsz : (i + 1) * c_rsz]
        key = struct.unpack("<III", rec[:12])
        race = key[0]
        if race in PLAYABLE_RACE_TAKEOVER:
            net_new_records.append(rec)
            race_takeovers_added += 1
            continue
        if key in auth_keys:
            overrides_dropped += 1
            continue
        net_new_records.append(rec)

    # No strings in this DBC, so the auth pool can be carried through as-is.
    out_body = b"".join(auth_kept) + b"".join(net_new_records)
    write_dbc(cust_path, a_fields, a_rsz, out_body, a_pool)

    print(
        f"  CharacterFacialHairStyles.dbc       base rows={len(auth_kept):6d}  "
        f"+net-new={len(net_new_records):4d}  "
        f"overrides dropped={overrides_dropped:5d}  "
        f"-> total={len(auth_kept) + len(net_new_records):6d}"
        f"  [race-takeover: -{auth_dropped_takeover} auth, +{race_takeovers_added} custom]"
    )


def hotfix_player_race_npc_extras() -> None:
    """Bind the mod-worgoblin player-race NPC wrapper displays to fresh
    CreatureDisplayInfoExtra rows so they actually have a Skin / Face / Hair
    assignment, instead of rendering as the textureless blue silhouette they
    ship as.

    Re-runnable: if a seeded Extra ID is already present in the Extra DBC,
    the row is REWRITTEN in place with the latest PLAYER_RACE_NPC_EXTRAS
    values (not just left alone). This is intentional so iterating on the
    safe Skin / Face / Hair indices doesn't require deleting the row by hand
    first - earlier revisions of this script seeded values that crashed the
    client (CharHairGeosets had no row for the chosen VariationID), and we
    want the same script run to be the way to roll the fix forward.

    Touches:
      CreatureDisplayInfo.dbc        - re-write ExtendedDisplayInfoID on each
                                       PLAYER_RACE_NPC_EXTRAS DisplayID
      CreatureDisplayInfoExtra.dbc   - upsert one row per seed
    """
    di_path = CUSTOM_DIR / "CreatureDisplayInfo.dbc"
    ex_path = CUSTOM_DIR / "CreatureDisplayInfoExtra.dbc"
    if not di_path.exists():
        sys.exit(f"missing: {di_path}")
    if not ex_path.exists():
        sys.exit(f"missing: {ex_path}")

    di_recs, di_fields, di_rsz, di_body, di_pool = read_dbc(di_path)
    ex_recs, ex_fields, ex_rsz, ex_body, ex_pool = read_dbc(ex_path)

    if di_rsz != 64 or di_fields != 16:
        sys.exit(
            f"CreatureDisplayInfo.dbc: unexpected layout "
            f"(fields={di_fields}, rec_size={di_rsz})"
        )
    if ex_fields != CDIE_FIELDS or ex_rsz != CDIE_REC_SIZE:
        sys.exit(
            f"CreatureDisplayInfoExtra.dbc: unexpected layout "
            f"(fields={ex_fields}, rec_size={ex_rsz})"
        )

    # Build the canonical row bytes for each seed entry.
    target_rows: dict[int, bytes] = {}  # ExtraID -> packed 84-byte row
    for (_did, ext_id, race, gender, skin, face, hair, hair_col, fhair) in PLAYER_RACE_NPC_EXTRAS:
        # 8 named cols + 11 NPCItemDisplayID + 1 Flags + 1 BakedSkinName.
        cols = [ext_id, race, gender, skin, face, hair, hair_col, fhair] \
            + [0] * 11 + [0, 0]
        assert len(cols) == CDIE_FIELDS, f"row width {len(cols)} != {CDIE_FIELDS}"
        target_rows[ext_id] = struct.pack(f"<{CDIE_FIELDS}I", *cols)

    # Walk existing Extra rows: rewrite any row whose ID we own (if bytes differ);
    # leave everything else untouched.
    ex_body_ba = bytearray(ex_body)
    rewritten = 0
    already_correct_extras = 0
    seen_existing: set[int] = set()
    for i in range(ex_recs):
        off = i * ex_rsz
        eid = struct.unpack("<I", ex_body_ba[off : off + 4])[0]
        if eid in target_rows:
            seen_existing.add(eid)
            new_row = target_rows[eid]
            if bytes(ex_body_ba[off : off + ex_rsz]) == new_row:
                already_correct_extras += 1
            else:
                ex_body_ba[off : off + ex_rsz] = new_row
                rewritten += 1

    # Append any seeds that didn't already have a row.
    appended_rows: list[bytes] = []
    for ext_id, row in target_rows.items():
        if ext_id not in seen_existing:
            appended_rows.append(row)
    if appended_rows:
        ex_body_ba.extend(b"".join(appended_rows))

    # Re-bind ExtendedDisplayInfoID on each target DisplayInfo row.
    di_body_ba = bytearray(di_body)
    want_extra: dict[int, int] = {did: eid for (did, eid, *_rest) in PLAYER_RACE_NPC_EXTRAS}
    rebound = 0
    already_correct_di = 0
    missing_displays: list[int] = list(want_extra.keys())
    for i in range(di_recs):
        rec_off = i * di_rsz
        did = struct.unpack("<I", di_body_ba[rec_off : rec_off + 4])[0]
        target = want_extra.get(did)
        if target is None:
            continue
        missing_displays.remove(did)
        cur_extra_off = rec_off + CDI_COL_EXTENDED * 4
        cur_extra = struct.unpack("<I", di_body_ba[cur_extra_off : cur_extra_off + 4])[0]
        if cur_extra == target:
            already_correct_di += 1
            continue
        struct.pack_into("<I", di_body_ba, cur_extra_off, target)
        rebound += 1

    if missing_displays:
        print(
            f"  WARNING: player-race wrapper DisplayIDs not found in "
            f"CreatureDisplayInfo.dbc: {sorted(missing_displays)}"
        )

    write_dbc(ex_path, ex_fields, ex_rsz, bytes(ex_body_ba), ex_pool)
    write_dbc(di_path, di_fields, di_rsz, bytes(di_body_ba), di_pool)

    print(
        f"  player-race NPC extras           "
        f"extras: +{len(appended_rows)} appended / ~{rewritten} rewritten / "
        f"={already_correct_extras} unchanged    "
        f"displays: ~{rebound} rebound / ={already_correct_di} unchanged    "
        f"(DisplayIDs {sorted(want_extra)})"
    )


def charsections_revert_jaw_fixup(path: Path) -> None:
    """Back out a previous blanket Texture[2] placeholder-fill pass.

    Walks every row, finds any Texture[2] string offset that points at
    `CHARSECTIONS_T2_PLACEHOLDER`, and zeros it back out so the row matches
    its original Patch-C HD-layer state. The string pool is left untouched
    (so the placeholder bytes may remain as orphaned dead weight - harmless,
    the client only follows live offsets).
    """
    if not path.exists():
        sys.exit(f"missing CharSections.dbc for revert: {path}")

    recs, fields, rec_size, body, pool = read_dbc(path)
    if fields != 10 or rec_size != 40:
        sys.exit(
            f"{path}: unexpected CharSections layout "
            f"(fields={fields}, rec_size={rec_size})"
        )

    placeholder_bytes = CHARSECTIONS_T2_PLACEHOLDER
    body_ba = bytearray(body)
    cleared = 0
    for i in range(recs):
        t2_off_pos = i * rec_size + 24
        t2_off = struct.unpack("<I", body_ba[t2_off_pos : t2_off_pos + 4])[0]
        if t2_off == 0:
            continue
        s = read_cstring_at(pool, t2_off)
        if s == placeholder_bytes:
            struct.pack_into("<I", body_ba, t2_off_pos, 0)
            cleared += 1

    if cleared == 0:
        print("  CharSections revert: no Texture[2] entries pointed at the placeholder, no change")
        return

    write_dbc(path, fields, rec_size, bytes(body_ba), pool)
    print(
        f"  CharSections revert: cleared {cleared} Texture[2] offsets that pointed at "
        f"{CHARSECTIONS_T2_PLACEHOLDER.decode()!r}"
    )


def main() -> int:
    revert_only = "--charsections-revert-jaw-fixup" in sys.argv[1:]

    if revert_only:
        print("Black Rose | hotfix: CharSections.dbc Texture[2] placeholder REVERT")
        print()
        charsections_revert_jaw_fixup(CUSTOM_DIR / "CharSections.dbc")
        print()
        print("Done. Surgically replace CharSections.dbc inside Patch-Z.MPQ with")
        print("`mpq_replace` to ship the revert.")
        return 0

    print("Black Rose | hotfix: rebuild mod-worgoblin creature/character DBCs from authoritative bases")
    print()
    for spec in SPECS:
        hotfix_one(spec)
    # Special case: CharacterFacialHairStyles.dbc has no PK column, so it
    # uses a composite-key merge pass instead of the generic hotfix_one().
    hotfix_charfacialhairstyles()
    # Player-race NPC wrapper DisplayIDs need ExtendedDisplayInfoID rows
    # (otherwise NPCs using the playable Goblin / Worgen models render as
    # textureless blue silhouettes).
    hotfix_player_race_npc_extras()
    print()
    print("Done. The mod-worgoblin creature/character DBC overrides have been replaced with")
    print("(Patch-F.MPQ / Patch-C.MPQ authoritative base) + (only the net-new mod-worgoblin rows).")
    print("Re-run `python3 build_patch.py merge` and repack Patch-Z.MPQ to ship the fix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
