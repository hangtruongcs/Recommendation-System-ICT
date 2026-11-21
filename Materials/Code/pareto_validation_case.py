"""One validation query from the existing pilot; no identifiers are emitted."""
from pathlib import Path
import json,numpy as np,pandas as pd
from final_test_jiaxing import ROOT,load_transactions,operational,train_bpr
D=load_transactions(ROOT/'28182251/Dataset/Charging_Data.csv'); train=D[D.start<'2021-07-01'];val=D[(D.start>='2021-07-01')&(D.start<'2021-10-01')].drop_duplicates('UserID');sites=sorted(train.site.unique());users=sorted(train.UserID.unique());si={s:i for i,s in enumerate(sites)};ui={u:i for i,u in enumerate(users)}
counts=np.zeros((len(users),len(sites)),np.int32)
for (u,s),n in train.groupby(['UserID','site']).size().items():counts[ui[u],si[s]]=n
q=val[val.UserID.isin(ui)&val.site.isin(si)].iloc[0]; P,Q,_=train_bpr(counts,8,np.random.default_rng(20261120));r=P[ui[q.UserID]]@Q.T; op=operational(train);o=op[op.end<pd.Timestamp('2021-07-01')];p=o[o.payment_time<pd.Timestamp('2021-07-01')];c=20*p.groupby('site').cost_rate.median().reindex(sites).to_numpy();d=20*o.groupby('site').minutes_rate.median().reindex(sites).to_numpy();z=np.column_stack([-r,c,d]);dom=(z[:,None,:]<=z[None,:,:]).all(2)&(z[:,None,:]<z[None,:,:]).any(2);remaining=np.ones(len(sites),bool);order=[];front=[]
while remaining.any():
 f=remaining&~(dom&remaining[:,None]).any(0);ids=np.flatnonzero(f);front.append(ids.tolist());order.extend(sorted(ids,key=lambda i:(-r[i],i)));remaining[f]=False
out={'scope':'validation exploratory first warm user, seed 20261120; anonymized query','sites':[{'site':sites[i],'relevance':float(r[i]),'cost_cny':float(c[i]),'duration_min':float(d[i]),'front':next(j+1 for j,x in enumerate(front) if i in x),'pareto_rank':order.index(i)+1,'bpr_rank':list(np.argsort(-r,kind='stable')).index(i)+1,'dominates':[sites[j] for j in np.flatnonzero(dom[i])]} for i in range(len(sites))]}
f=Path(__file__).parent/'pilot_results'/'pareto_validation_case.json';f.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(out,indent=2,ensure_ascii=False))
