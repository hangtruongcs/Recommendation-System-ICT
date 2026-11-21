"""Post-hoc MAE of per-kWh estimators on observed test sessions."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from final_test_jiaxing import ROOT, load_transactions, operational

df = load_transactions(ROOT / '28182251/Dataset/Charging_Data.csv')
train = df[df.start < '2021-07-01']
test = operational(df[df.start >= '2021-10-01'])
cutoff = pd.Timestamp('2021-07-01')
train_valid = operational(train)
duration = train_valid[train_valid.end < cutoff]
cost = duration[duration.payment_time < cutoff]
site_cost = cost.groupby('site').cost_rate.median()
site_duration = duration.groupby('site').minutes_rate.median()
valid = test[test.site.isin(site_cost.index) & test.site.isin(site_duration.index)]
result = {
    'test_sessions': len(valid),
    'site_cost_rate_mae_cny_per_kwh': float(np.mean(abs(valid.cost_rate - valid.site.map(site_cost)))),
    'global_cost_rate_mae_cny_per_kwh': float(np.mean(abs(valid.cost_rate - cost.cost_rate.median()))),
    'site_duration_rate_mae_minutes_per_kwh': float(np.mean(abs(valid.minutes_rate - valid.site.map(site_duration)))),
    'global_duration_rate_mae_minutes_per_kwh': float(np.mean(abs(valid.minutes_rate - duration.minutes_rate.median()))),
}
path = Path(__file__).parent / 'pilot_results' / 'final_test' / 'unit_rate_errors_posthoc.json'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
