#!/usr/bin/env python3
"""Build the Black Rose client DBC patch.

Three modes:

  customonly   Build DBC files containing ONLY the custom Black Rose rows.
               Useful for validating the binary writer; NOT a drop-in client
               patch on its own (it would replace the client's full Spell.dbc
               with three rows and break every other spell). Output goes to
               staging/DBFilesClient/.

  merge        Combine the three input layers into staging/ AND pack the
               result into output/patch-Z.MPQ:
                 1. input/stock/DBFilesClient/  - vanilla 3.3.5a DBCs the user
                    extracted from their reference client (gitignored, this
                    is copyrighted Blizzard data).
                 2. input/custom/               - our committed custom tree
                    (mod-worgoblin's race assets + pre-patched DBCs, plus
                    Black Rose's BLP item icons under Interface/Icons/).
                 3. definitions/*.json         - Black Rose row overlays
                    upserted into the nine DBCs they touch.
               Pass --no-pack to stop after staging/ is populated.

  pack         Skip the merge and pack whatever is currently under staging/
               into output/patch-Z.MPQ. Useful for re-packing after a
               manual tweak to a staged file.

Usage:
  python3 build_patch.py customonly
  python3 build_patch.py merge [--no-pack]
  python3 build_patch.py pack
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import dbc
import mpq


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
DEF_DIR = HERE / "definitions"
STOCK_DBC_DIR = HERE / "input" / "stock" / "DBFilesClient"
CUSTOM_DIR = HERE / "input" / "custom"
STAGING_ROOT = HERE / "staging"
STAGING_DBC_DIR = STAGING_ROOT / "DBFilesClient"
OUTPUT_DIR = HERE / "output"
OUTPUT_MPQ = OUTPUT_DIR / "patch-Z.MPQ"


DEFINITION_TO_SCHEMA = {
    "spell": "spell",
    "spellduration": "spellduration",
    "spellitemenchantment": "spellitemenchantment",
    "gemproperties": "gemproperties",
    "itemextendedcost": "itemextendedcost",
    "skilllineability": "skilllineability",
    "questsort": "questsort",
    "item": "item",
    "itemdisplayinfo": "itemdisplayinfo",
}


def load_definition(name: str) -> list[dict]:
    path = DEF_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing definition: {path}")
    return json.loads(path.read_text())


def base_dbc_path(filename: str) -> Path | None:
    """Effective base DBC for a given filename.

    Resolution order:
      1. input/custom/DBFilesClient/<filename> - if we ship a pre-patched
         copy (e.g. mod-worgoblin's modified ChrRaces.dbc / Item.dbc /
         Spell.dbc / ...), that becomes the base layer the JSON overlay
         merges on top of.
      2. input/stock/DBFilesClient/<filename>  - vanilla Blizzard DBC the
         user extracted from their reference client.

    Returns None if neither layer ships the file - caller decides whether
    that is fatal.
    """
    custom_candidate = CUSTOM_DIR / "DBFilesClient" / filename
    if custom_candidate.is_file():
        return custom_candidate
    stock_candidate = STOCK_DBC_DIR / filename
    return stock_candidate if stock_candidate.is_file() else None


def copy_custom_assets() -> tuple[int, int]:
    """Mirror input/custom/ into staging/.

    Returns (file_count, passthrough_dbc_count). DBCs that a Black Rose
    JSON definition targets are NOT copied straight through here - they
    will be re-emitted by build_merge() once the JSON overlay has been
    applied on top of whichever layer (custom or stock) supplied the
    base. DBCs that no definition touches (the other 20+ DBCs
    mod-worgoblin patches: ChrRaces, CharSections, CreatureDisplayInfo,
    etc.) are copied verbatim into staging/DBFilesClient/.

    All non-DBC files (M2 / skin / blp / anim / ogg / lua / xml /
    textures / ...) are always copied through.
    """
    overlay_dbc_filenames = {
        dbc.SCHEMAS[schema_name].filename
        for schema_name in DEFINITION_TO_SCHEMA.values()
    }
    # Blizzard glue / FrameXML scripts that the upstream module ships are
    # NOT packed. These files override stock Blizzard UI scripts and only
    # work on the specific 3.3.5a build the upstream author tested
    # against (~build 12340 with their local cache state). On a different
    # client patch level or a freshly-cleared Cache/, the override
    # references a missing global or widget kit and the parser bails out
    # with 'Your login interface files are corrupt please reinstall the
    # game' before the login screen even renders. The race-creation UI
    # works fine on the stock CharacterCreate.lua because ChrRaces.dbc /
    # CharSections.dbc / etc. already drive race enumeration there - the
    # custom override is a polish item, not a hard requirement, so we
    # leave it on the floor until it can be reauthored cleanly.
    UI_SKIP_RELATIVE_PATHS = {
        Path("Interface/GlueXML/CharacterCreate.lua"),
        Path("Interface/GlueXML/CharacterCreate.xml"),
        Path("Interface/GlueXML/GlueStrings.lua"),
        Path("Interface/GlueXML/GlueParent.lua"),
        Path("Interface/FrameXML/PetPaperDollFrame.lua"),
    }
    file_count = 0
    passthrough_dbc_count = 0
    skipped_ui = 0
    if not CUSTOM_DIR.is_dir():
        return (0, 0)
    for src in CUSTOM_DIR.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(CUSTOM_DIR)
        if (
            rel.parts[:1] == ("DBFilesClient",)
            and rel.name in overlay_dbc_filenames
        ):
            continue
        if rel in UI_SKIP_RELATIVE_PATHS:
            skipped_ui += 1
            continue
        dst = STAGING_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        file_count += 1
        if rel.parts[:1] == ("DBFilesClient",):
            passthrough_dbc_count += 1
    if skipped_ui:
        print(
            f"  skipped {skipped_ui} upstream UI script override(s)"
            " (Blizzard glue/FrameXML; see copy_custom_assets() comment)"
        )
    return file_count, passthrough_dbc_count


def validate_itemdisplay_icons() -> None:
    """Verify custom ItemDisplayInfo rows point at staged BLP icons."""
    schema = dbc.SCHEMAS["itemdisplayinfo"]
    dbc_path = STAGING_DBC_DIR / schema.filename
    if not dbc_path.exists():
        sys.exit(f"ERROR: missing staged DBC {dbc_path.relative_to(HERE)}")

    staged_dbc = dbc.read_dbc(dbc_path, schema)
    staged_rows = {int(row["ID"]): row for row in staged_dbc.rows}
    missing_rows: list[int] = []
    missing_icons: list[str] = []

    for expected in load_definition("itemdisplayinfo"):
        display_id = int(expected["ID"])
        icon_name = str(expected["InventoryIcon_1"])
        row = staged_rows.get(display_id)
        if not row or row.get("InventoryIcon_1") != icon_name:
            missing_rows.append(display_id)
            continue

        icon_path = STAGING_ROOT / "Interface" / "Icons" / f"{icon_name}.blp"
        if not icon_path.exists():
            missing_icons.append(str(icon_path.relative_to(HERE)))

    if missing_rows:
        joined = ", ".join(str(display_id) for display_id in missing_rows)
        sys.exit(f"ERROR: missing ItemDisplayInfo rows in staged DBC: {joined}")
    if missing_icons:
        joined = "\n  ".join(missing_icons)
        sys.exit(f"ERROR: missing staged icon BLP(s):\n  {joined}")

    print("  validated ItemDisplayInfo icons in staging/")


def build_customonly() -> None:
    STAGING_DBC_DIR.mkdir(parents=True, exist_ok=True)
    for def_name, schema_name in DEFINITION_TO_SCHEMA.items():
        schema = dbc.SCHEMAS[schema_name]
        rows = load_definition(def_name)
        out = dbc.DbcFile(schema=schema, rows=rows)
        out.sort_by_id()
        target = STAGING_DBC_DIR / schema.filename
        dbc.write_dbc(out, target)
        print(f"  wrote {target.relative_to(HERE)}  rows={len(rows)}")
    print("\nDONE. staging/DBFilesClient/ contains the custom-only DBCs.")
    print("These are NOT a usable client patch on their own - they would")
    print("replace the full client DBCs with only Black Rose rows. Use the")
    print("'merge' mode for distribution.")


def pack_mpq(staging_root: Path = STAGING_ROOT, output_path: Path = OUTPUT_MPQ) -> tuple[int, int]:
    """Pack every file under staging/ into a v1 MPQ at output/patch-Z.MPQ.

    Self-verifies by reopening the freshly-written archive, decoding its
    tables, and round-tripping one file's bytes against the staged source.
    Returns (file_count_including_listfile, archive_size_bytes).
    """
    if not staging_root.is_dir():
        sys.exit(f"ERROR: {staging_root.relative_to(HERE)}/ does not exist; run merge first")

    writer = mpq.MpqWriter(output_path)
    added = writer.add_directory(staging_root)
    if added == 0:
        sys.exit(f"ERROR: no files under {staging_root.relative_to(HERE)}/ to pack")
    files, size = writer.write()
    rel = output_path.relative_to(HERE)
    print(f"  packed {added} file(s) + (listfile) -> {rel} ({size:,} bytes)")

    # Self-verify: open the freshly written archive and read one file back.
    # Picks a small file to keep the round-trip cheap, but if there isn't
    # one we still validate header + tables decoded cleanly.
    with mpq.MpqReader(output_path) as r:
        if r.block_table_size != added + 1:
            sys.exit(
                "ERROR: round-trip mismatch:"
                f" block_table_size={r.block_table_size}, expected {added + 1}"
            )
        sample = sorted(staging_root.rglob("*"))
        sample = [p for p in sample if p.is_file() and p.stat().st_size < 65536]
        if sample:
            probe = sample[0]
            rel_in_mpq = probe.relative_to(staging_root).as_posix().replace('/', '\\')
            staged_bytes = probe.read_bytes()
            mpq_bytes = r.read(rel_in_mpq)
            if mpq_bytes != staged_bytes:
                sys.exit(
                    f"ERROR: round-trip mismatch on {rel_in_mpq}:"
                    f" staged={len(staged_bytes)} bytes, mpq={len(mpq_bytes)} bytes"
                )
            print(f"  self-verified {rel_in_mpq} ({len(staged_bytes)} bytes)")
    return files, size


def build_merge(pack: bool = True) -> None:
    if not STOCK_DBC_DIR.exists():
        sys.exit(
            f"ERROR: {STOCK_DBC_DIR.relative_to(HERE)} does not exist.\n"
            "Extract the client base DBCs into that folder first.\n"
            "See README.md > Extracting stock DBCs."
        )
    STAGING_DBC_DIR.mkdir(parents=True, exist_ok=True)

    custom_files, passthrough_dbc_count = copy_custom_assets()
    if custom_files:
        print(
            f"  copied {custom_files} custom asset(s) into staging/"
            f" ({passthrough_dbc_count} DBC{'s' if passthrough_dbc_count != 1 else ''}"
            " straight-copied; overlay DBCs are merged below)"
        )

    for def_name, schema_name in DEFINITION_TO_SCHEMA.items():
        schema = dbc.SCHEMAS[schema_name]
        custom_rows = load_definition(def_name)
        base_path = base_dbc_path(schema.filename)
        if base_path is None:
            sys.exit(
                f"ERROR: no base for {schema.filename}.\n"
                f"  Looked in {(CUSTOM_DIR / 'DBFilesClient').relative_to(HERE)}/"
                f" and {STOCK_DBC_DIR.relative_to(HERE)}/.\n"
                "  Extract the stock DBC from the client (see README.md)."
            )
        # Annotate the merge log so it's obvious which layer the base came from.
        try:
            base_label = base_path.relative_to(ROOT).as_posix()
        except ValueError:
            base_label = base_path.name
        merged = dbc.read_dbc(base_path, schema)
        before = len(merged.rows)
        merge_count = 0
        for row in custom_rows:
            # _merge=true means "override only the keys in this entry on
            # top of the existing stock row" - used to retune a couple
            # of fields (e.g. EffectBasePoints) on a stock spell without
            # dropping its visual/school/target geometry to zero, which
            # is what a full upsert would do.
            if row.pop("_merge", False):
                merged.merge_row(row)
                merge_count += 1
            else:
                merged.upsert(row)
        merged.sort_by_id()
        target = STAGING_DBC_DIR / schema.filename
        dbc.write_dbc(merged, target)
        added = len(merged.rows) - before
        print(
            f"  {schema.filename:30}"
            f" base={before:6d}"
            f" custom={len(custom_rows):4d}"
            f" added={added:4d}"
            f" merged={merge_count:3d}"
            f" total={len(merged.rows):6d}"
            f"   <- {base_label}"
        )

    validate_itemdisplay_icons()
    if pack:
        print()
        pack_mpq()
        print(f"\nDONE. {OUTPUT_MPQ.relative_to(HERE)} is ready to drop in the client.")
    else:
        print("\nDONE. staging/ is populated; --no-pack skipped MPQ creation.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=["customonly", "merge", "pack"],
        help="customonly: write only Black Rose rows; "
        "merge: stock + custom + JSON overlays into staging/ (and pack); "
        "pack: pack staging/ into output/patch-Z.MPQ without re-merging",
    )
    parser.add_argument(
        "--no-pack",
        action="store_true",
        help="In 'merge' mode, stop after staging/ is populated and skip MPQ packing.",
    )
    args = parser.parse_args()
    if args.mode == "customonly":
        build_customonly()
    elif args.mode == "merge":
        build_merge(pack=not args.no_pack)
    else:
        pack_mpq()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
