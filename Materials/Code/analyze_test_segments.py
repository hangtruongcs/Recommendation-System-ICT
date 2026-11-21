"""Post hoc descriptive test analysis; reproduces fixed train and ranking."""
from pathlib import Path
import json,sys,hashlib,platform
import numpy as np
import pandas as pd
from final_test_jiaxing import ROOT, load_transactions, operational, train_bpr, scale
out=Path(__file__).parent/'pilot_results'/'final_test';path=ROOT/'28182251/Dataset/Charging_Data.csv'
df=load_transactions(path); train=df[df.start<'2021-07-01']; test=df[df.start>='2021-10-01'].drop_duplicates('UserID')
sites=sorted(train.site.unique()); users=sorted(train.UserID.unique());si={s:i for i,s in enumerate(sites)};ui={u:i for i,u in enumerate(users)}
counts=np.zeros((len(users),len(sites)),dtype=np.int32)
for (u,s),n in train.groupby(['UserID','site']).size().items():counts[ui[u],si[s]]=n
q=test[test.UserID.isin(ui)&test.site.isin(si)];idx=np.array([ui[u] for u in q.UserID]);target=np.array([si[s] for s in q.site]);repeat=counts[idx,target]>0
oper=operational(train);cut=pd.Timestamp('2021-07-01');dur=oper[oper.end<cut];pay=dur[dur.payment_time<cut]
c=20*pay.groupby('site').cost_rate.median().reindex(sites).to_numpy();d=20*dur.groupby('site').minutes_rate.median().reindex(sites).to_numpy();pop=counts.sum(0)
def pareto(r):
 z=np.column_stack([-r,c,d]);dom=(z[:,None,:]<=z[None,:,:]).all(2)&(z[:,None,:]<z[None,:,:]).any(2);rem=np.ones(len(sites),bool);o=[]
 while rem.any():
  front=rem & ~(dom&rem[:,None]).any(0);ids=np.flatnonzero(front);o.extend(sorted(ids,key=lambda i:(-r[i],i)));rem[front]=False
 return np.array(o)
res={'scope':'post hoc descriptive test; no model selection','users':len(q),'repeat':int(repeat.sum()),'new_to_user':int((~repeat).sum()),'seeds':{}}
for seed in [20261120,20261121,20261122]:
 P,Q,_=train_bpr(counts,8,np.random.default_rng(seed));r=P[idx]@Q.T; orders={'personal_frequency':np.argsort(-(counts[idx]+(pop/(pop.max()+1))*1e-6),axis=1,kind='stable'),'bpr_mf':np.argsort(-r,axis=1,kind='stable'),'weighted_sum':np.argsort(-(.5*scale(r)-.25*scale(c)-.25*scale(d)),axis=1,kind='stable'),'pareto_front_relevance':np.vstack([pareto(row) for row in r])}
 row={}
 saved=json.loads((out/f'results_dim_8_seed_{seed}_availability_proxy.json').read_text())
 for name,order in orders.items():
  ranks=np.argmax(order==target[:,None],axis=1)+1;nd=np.where(ranks<=3,1/np.log2(ranks+1),0)
  assert abs(nd.mean()-saved['methods'][name]['ranking']['3']['ndcg'])<1e-12
  row[name]={'position_metrics': [{'rank':k+1,'cost':float(c[order[:,k]].mean()),'duration':float(d[order[:,k]].mean()),'target_fraction':float((ranks==k+1).mean())} for k in range(5)], 'repeat':{'n':int(repeat.sum()),'ndcg3':float(nd[repeat].mean()),'hit3':float((ranks[repeat]<=3).mean())},'new_to_user':{'n':int((~repeat).sum()),'ndcg3':float(nd[~repeat].mean()),'hit3':float((ranks[~repeat]<=3).mean())},'list_cost_top3':float(c[order[:,:3]].mean()),'list_duration_top3':float(d[order[:,:3]].mean())}
 row['pareto_vs_weighted_overlap']={str(k):float(np.mean([len(set(a[:k]) & set(b[:k]))/k for a,b in zip(orders['pareto_front_relevance'],orders['weighted_sum'])])) for k in (1,3,5)}
 res['seeds'][str(seed)]=row;print('seed',seed,flush=True)
(out/'segments_and_list_metrics_posthoc.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
