import pandas as pd
import numpy as np

obs = pd.read_csv('data/audit/frame_observations.csv')
obs.rename(columns={'tracker_id': 'track_id'}, inplace=True)
print('Total observations:', len(obs), '| Unique tracks:', obs['track_id'].nunique())

def get_track_stats(tid):
    t = obs[obs['track_id'] == tid].sort_values('frame_idx').copy()
    first_f = int(t.iloc[0]['frame_idx'])
    last_f = int(t.iloc[-1]['frame_idx'])
    cls = t.iloc[0]['class_name']
    t['cx'] = (t['x1'] + t['x2']) / 2.0
    t['cy'] = (t['y1'] + t['y2']) / 2.0
    return t, first_f, last_f, cls

def eval_pair(t1_id, t2_id, verbose=True):
    t1, f1_start, f1_end, cls1 = get_track_stats(t1_id)
    t2, f2_start, f2_end, cls2 = get_track_stats(t2_id)
    gap = f2_start - f1_end
    tail = t1.tail(min(5, len(t1)))
    if len(tail) >= 2:
        df = tail.iloc[-1]['frame_idx'] - tail.iloc[0]['frame_idx']
        vx = (tail.iloc[-1]['cx'] - tail.iloc[0]['cx']) / df if df > 0 else 0.0
        vy = (tail.iloc[-1]['cy'] - tail.iloc[0]['cy']) / df if df > 0 else 0.0
    else:
        vx, vy = 0.0, 0.0
    
    pred_cx = tail.iloc[-1]['cx'] + vx * gap
    pred_cy = tail.iloc[-1]['cy'] + vy * gap
    
    head = t2.head(min(5, len(t2)))
    act_cx = head.iloc[0]['cx']
    act_cy = head.iloc[0]['cy']
    
    dist = float(np.sqrt((pred_cx - act_cx)**2 + (pred_cy - act_cy)**2))
    raw_dist = float(np.sqrt((tail.iloc[-1]['cx'] - act_cx)**2 + (tail.iloc[-1]['cy'] - act_cy)**2))
    
    if len(head) >= 2:
        df2 = head.iloc[-1]['frame_idx'] - head.iloc[0]['frame_idx']
        vx2 = (head.iloc[-1]['cx'] - head.iloc[0]['cx']) / df2 if df2 > 0 else 0.0
        vy2 = (head.iloc[-1]['cy'] - head.iloc[0]['cy']) / df2 if df2 > 0 else 0.0
    else:
        vx2, vy2 = 0.0, 0.0
        
    mag1 = np.sqrt(vx**2 + vy**2)
    mag2 = np.sqrt(vx2**2 + vy2**2)
    cos = float((vx * vx2 + vy * vy2) / (mag1 * mag2)) if (mag1 > 1e-3 and mag2 > 1e-3) else None
        
    if verbose:
        cos_str = f'{cos:.2f}' if cos is not None else 'N/A'
        print(f'Pair {t1_id:2d}->{t2_id:2d} ({cls1:14s}): gap={gap:2d}f (f{f1_end}->f{f2_start}) | pred_dist={dist:6.1f}px (raw={raw_dist:6.1f}px) | cos={cos_str} | v1=({vx:5.1f},{vy:5.1f}) v2=({vx2:5.1f},{vy2:5.1f})')
    return {'t1': t1_id, 't2': t2_id, 'cls': cls1, 'gap': gap, 'pred_dist': dist, 'raw_dist': raw_dist, 'cos': cos}

print('\n=== TARGET KNOWN-SAME PAIRS ===')
eval_pair(4, 6)
eval_pair(14, 16)

print('\n=== ALL TEMPORAL GAP CANDIDATES (gap <= 25, same class) ===')
track_ids = sorted(obs['track_id'].unique())
for tid1 in track_ids:
    t1, s1, e1, c1 = get_track_stats(tid1)
    for tid2 in track_ids:
        if tid1 == tid2: continue
        t2, s2, e2, c2 = get_track_stats(tid2)
        if c1 == c2 and 0 < (s2 - e1) <= 25:
            eval_pair(tid1, tid2)
