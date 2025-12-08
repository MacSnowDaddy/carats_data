import argparse
from pathlib import Path
import glob
import sys
from typing import List, Optional

import pandas as pd

from airport_guesser import AirportGuesser

def collect_trk_paths(inputs: List[str], dates: Optional[List[str]], source_times: Optional[List[str]], trk_dir: Optional[str]) -> List[str]:
    """
    inputs が指定されていればそれを優先（ファイル/ワイルドカード可）。
    dates+source_times+trk_dir が指定されていればそこからファイルパスを生成。
    """
    paths = []
    if inputs:
        for p in inputs:
            # glob パターンや単一ファイルに対応
            expanded = glob.glob(str(Path(p).expanduser()))
            paths.extend(expanded)
    if dates and source_times and trk_dir:
        for d in dates:
            for st in source_times:
                paths.append(str(Path(trk_dir).expanduser() / f"trk{d}_{st}.csv"))
    # 存在するファイルだけ返す
    return [p for p in paths if Path(p).exists()]

def parse_comma_list(s: Optional[str]) -> Optional[List[str]]:
    if not s:
        return None
    return [x.strip() for x in s.split(',') if x.strip()]

def main(argv=None):
    parser = argparse.ArgumentParser(description="Annotate trk CSVs with Entry/Exit points using AirportGuesser.")
    parser.add_argument('--input', '-i', nargs='*', help='trk CSV file(s) or glob patterns. e.g. ~/Desktop/201908/*.csv')
    parser.add_argument('--dates', '-d', help='Comma-separated dates like 20190816,20190817 (used with --source-times and --trk-dir)')
    parser.add_argument('--source-times', '-s', help='Comma-separated source times like 00_12,12_18')
    parser.add_argument('--trk-dir', help='Directory where trkYYYYMMDD_source.csv live (used with --dates)')
    parser.add_argument('--airport-file', '-a', required=True, help='Aerodrome file (tsv style) used by AirportGuesser')
    parser.add_argument('--fixes-file', help='Optional fixes file (tsv style)')
    parser.add_argument('--target-airports', help='Comma-separated list of ICAO to restrict guessing (optional)')
    parser.add_argument('--radius', '-r', type=float, default=10.0, help='radius_km used for assignment (default: 10.0)')
    parser.add_argument('--output', '-o', required=True, help='Output CSV path (annotated trks or guess summary)')
    parser.add_argument('--include-trks', action='store_true', help='If set, write full trk rows with EntryPoint/ExitPoint appended.')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    args = parser.parse_args(argv)

    dates = parse_comma_list(args.dates)
    source_times = parse_comma_list(args.source_times)
    target_airports = parse_comma_list(args.target_airports)

    paths = collect_trk_paths(args.input or [], dates, source_times, args.trk_dir)
    if args.verbose:
        print(f"Collected {len(paths)} trk files")

    g = AirportGuesser(airport_file=str(Path(args.airport_file).expanduser()),
                       fixes_file=(str(Path(args.fixes_file).expanduser()) if args.fixes_file else None),
                       target_airports=target_airports)
    if paths:
        g.load_trks_from_paths(paths)
    elif dates and source_times and args.trk_dir:
        g.load_trks_from_dates(dates, source_times, trk_dir=args.trk_dir)
    else:
        print("No trk input provided. Use --input or (--dates and --source-times and --trk-dir).", file=sys.stderr)
        sys.exit(2)

    g.preprocess()
    g.assign(radius_km=args.radius)
    g.to_csv(args.output, include_trks=args.include_trks, include_date=True)
    if args.verbose:
        print(f"Wrote {args.output}")

if __name__ == '__main__':
    main()