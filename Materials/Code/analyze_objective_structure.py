"""Phân tích mô tả sau khi xem test; tái tạo mô hình theo giao thức đã cố định."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr
from final_test_jiaxing import ROOT, load_transactions, operational, train_bpr

OUT=Path(__file__).resolve().parent/'pilot_results'/'final_test'
df=load_transactions(ROOT/'28182251/Dataset/Charging_Data.csv')
train=df[df.start<'2021-07-01'].copy()
test=df[df.start>='2021-10-01'].drop_duplicates('UserID').copy()
sites=sorted(train.site.unique()); users=sorted(train.UserID.unique())
si={s:i for i,s in enumerate(sites)}; ui={u:i for i,u in enumerate(users)}
counts=np.zeros((len(users),len(sites)),dtype=np.int32)
for (u,s),n in train.groupby(['UserID','site']).size().items(): counts[ui[u],si[s]]=n
q=test[test.UserID.isin(ui)&test.site.isin(si)]
qids=np.array([ui[u] for u in q.UserID]); target=np.array([si[x] for x in q.site])
oper=operational(train); cutoff=pd.Timestamp('2021-07-01')
dur=oper[oper.end<cutoff]; cost=dur[dur.payment_time<cutoff]
agg=pd.DataFrame({'cost':cost.groupby('site').cost_rate.median(),'duration':dur.groupby('site').minutes_rate.median()}).reindex(sites)
c=agg.cost.to_numpy(); d=agg.duration.to_numpy()
rc,rd=rankdata(c),rankdata(d)
def rankcorr(x,y):
 x=x-x.mean(axis=1,keepdims=True); y=y-y.mean(); den=np.sqrt((x*x).sum(axis=1)*(y*y).sum())
 return np.divide(x@y,den,out=np.full(len(x),np.nan),where=den!=0)
def summarize(x, seed):
 x=np.asarray(x,dtype=float); x=x[np.isfinite(x)]; rng=np.random.default_rng(seed)
 boots=np.array([np.median(rng.choice(x,size=len(x),replace=True)) for _ in range(1000)])
 return {'n':len(x),'median':float(np.median(x)),'q25':float(np.quantile(x,.25)),'q75':float(np.quantile(x,.75)), 'median_bootstrap95':np.quantile(boots,[.025,.975]).tolist()}
res={'scope':'post hoc descriptive test analysis; not a new independent test','users':len(q),'sites':len(sites), 'cost_duration_spearman':float(spearmanr(c,d).statistic),'seeds':{}}
for seed in (20261120,20261121,20261122):
 P,Q,_=train_bpr(counts,8,np.random.default_rng(seed)); scores=P[qids]@Q.T
 ranks=rankdata(scores,axis=1); a=rankcorr(ranks,rc); b=rankcorr(ranks,rd)
 first=[]; layers_n=[]; dominance=[]; overlap={k:[] for k in (1,3,5)}; front_by_k={k:[] for k in (1,3,5)}; ties=0; nd=[]; nd_pareto=[]
 for r,t in zip(scores,target):
  z=np.column_stack([-r,c,d]); dom=(z[:,None,:]<=z[None,:,:]).all(2)&(z[:,None,:]<z[None,:,:]).any(2)
  rem=np.ones(len(sites),dtype=bool); layers=[]; layers_map=np.zeros(len(sites),dtype=int)
  while rem.any():
   front=rem & ~(dom & rem[:,None]).any(axis=0); ids=np.flatnonzero(front); layers_map[ids]=len(layers)+1; layers.append(ids); rem[front]=False
  order=np.array([i for layer in layers for i in sorted(layer,key=lambda i:(-r[i],i))]); bpr=np.argsort(-r,kind='stable')
  first.append(len(layers[0])); layers_n.append(len(layers)); dominance.append(dom.sum()/(len(sites)*(len(sites)-1)/2)); ties+=int(np.sum(r==np.max(r))>1)
  rank=np.where(bpr==t)[0][0]+1; nd.append(1/np.log2(rank+1) if rank<=3 else 0)
  rank_p=np.where(order==t)[0][0]+1; nd_pareto.append(1/np.log2(rank_p+1) if rank_p<=3 else 0)
  for k in overlap:
   overlap[k].append(len(set(order[:k])&set(bpr[:k]))/k);front_by_k[k].append([int((layers_map[order[:k]]==j).sum()) for j in range(1,6)])
 saved=json.loads((OUT/f'results_dim_8_seed_{seed}_availability_proxy.json').read_text())
 assert abs(np.mean(nd)-saved['methods']['bpr_mf']['ranking']['3']['ndcg'])<1e-12
 assert abs(np.mean(nd_pareto)-saved['methods']['pareto_front_relevance']['ranking']['3']['ndcg'])<1e-12
 res['seeds'][str(seed)]={'relevance_cost_spearman':summarize(a,1000+seed),'relevance_duration_spearman':summarize(b,2000+seed), 'first_front_mean':float(np.mean(first)), 'first_front_median':float(np.median(first)), 'first_front_fraction_mean':float(np.mean(first)/len(sites)), 'fronts_mean':float(np.mean(layers_n)), 'dominant_pair_fraction_mean':float(np.mean(dominance)), 'top_k_overlap_mean':{str(k):float(np.mean(v)) for k,v in overlap.items()},'top_k_front_distribution_mean_counts':{str(k):np.mean(v,axis=0).tolist() for k,v in front_by_k.items()},'top_score_ties':ties}
 print('seed',seed,flush=True)
(OUT/'objective_structure_posthoc.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(res,indent=2))
