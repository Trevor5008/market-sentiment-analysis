#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
import pandas as pd

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--new', required=True, help='New snapshot CSV')
    p.add_argument('--dest', required=True, help='Accumulated CSV')
    p.add_argument('--manifest', required=True, help='Manifest JSON')
    p.add_argument('--key', default='', help='Dedupe key columns')
    args = p.parse_args()
    
    if not os.path.exists(args.new):
        print(f"ERROR: file not found: {args.new}")
        return 1
    
    df_new = pd.read_csv(args.new)
    rows_new = len(df_new)
    
    if os.path.exists(args.dest):
        df_acc = pd.read_csv(args.dest)
        rows_before = len(df_acc)
        df_combined = pd.concat([df_acc, df_new], ignore_index=True)
    else:
        rows_before = 0
        df_combined = df_new
    
    key_cols = [k.strip() for k in args.key.split(',')] if args.key else None
    if key_cols:
        df_out = df_combined.drop_duplicates(subset=key_cols, keep='last')
    else:
        df_out = df_combined.drop_duplicates(keep='last')
        
    rows_after = len(df_out)
    # Save accumulated CSV
    os.makedirs(os.path.dirname(args.dest) or '.', exist_ok=True)
    df_out.to_csv(args.dest, index=False)
    
    #Update the manifest
    m = {}
    if os.path.exists(args.manifest):
        with open(args.manifest) as f:
            m = json.load(f)
            
    m['accumulation'] = {
        'rows_before': rows_before,
        'rows_new': rows_new,
        'rows_after': rows_after,
        'runs': m.get('accumulation', {}).get('runs', 0) + 1,
        'last_run': datetime.now(timezone.utc).isoformat()
    }
    with open(args.manifest, 'w') as f:
        json.dump(m, f, indent=2)

    print(f"ACCUMULATE: before={rows_before} new={rows_new} after={rows_after}")
    return 0

if __name__ == '__main__':
    main()