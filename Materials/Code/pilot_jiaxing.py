"""Exploratory Jiaxing pilot; train through June 2021, validate July–September.

All visits count for relevance. Operational estimators use positive energy and
duration, including all termination classes. Test is audited but not evaluated.
"""
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'pilot_results'
def load_transactions(data_path):
    """Đọc giao dịch, chuẩn hóa site key và sắp xếp theo thời gian.

    Không sửa CSV gốc. Lỗi timestamp làm dừng thực nghiệm thay vì loại ngầm dữ liệu.
    """
    cols = ['UserID', 'District Name', 'Location Information', 'Start Time', 'End Time', 'Payment time',
            'Transaction power/kwh', 'Actual Payment/Yuan', 'Transaction Amount/Yuan', 'is_abnormal']
    df = pd.read_csv(data_path, encoding='gb18030', usecols=cols)
    for col in ['District Name', 'Location Information', 'Start Time', 'End Time', 'Payment time']:
        df[col] = df[col].str.strip()
    df['start'] = pd.to_datetime(df['Start Time'], errors='coerce')
    df['end'] = pd.to_datetime(df['End Time'], errors='coerce')
    df['payment_time'] = pd.to_datetime(df['Payment time'], errors='coerce')
    df['site'] = df['District Name'] + ' | ' + df['Location Information']
    df = df.sort_values(['start', 'UserID', 'site'], kind='stable').reset_index(drop=True)
    if not df['start'].notna().all() or not df['end'].notna().all() or not df['payment_time'].notna().all():
        raise ValueError('Không thể phân tích một hoặc nhiều timestamp.')
    return df


def train_bpr(counts, dimensions, rng):
    """Huấn luyện BPR-MF từ ma trận số lượt và bộ sinh ngẫu nhiên.

    Cạnh dương là lượt ghé nhị phân; negative là địa điểm chưa quan sát.
    Trả về vector người dùng, địa điểm và chỉ số người dùng có thể lấy mẫu.
    Cấu hình pilot cố định ở 20 epoch, 100 batch và 1.024 mẫu mỗi batch.
    """
    n, m = counts.shape
    # Train binary-edge BPR-MF using uniform user, positive, and unobserved sampling.
    eligible = np.where((counts > 0).sum(axis=1) < m)[0]
    P = rng.normal(0, .05, (n, dimensions))
    Q = rng.normal(0, .05, (m, dimensions))
    possets = [np.flatnonzero(row) for row in counts]
    negsets = [np.flatnonzero(row == 0) for row in counts]
    for epoch in range(20):
        for _ in range(100):
            batch_u = rng.choice(eligible, size=1024)
            ip = np.array([rng.choice(possets[u]) for u in batch_u])
            jn = np.array([rng.choice(negsets[u]) for u in batch_u])
            pu, qi, qj = P[batch_u].copy(), Q[ip].copy(), Q[jn].copy()
            gap = np.sum(pu * (qi-qj), axis=1)
            g = 1 / (1 + np.exp(np.clip(gap, -30, 30)))
            np.add.at(P, batch_u, .03*(g[:,None]*(qi-qj)-.001*pu))
            np.add.at(Q, ip, .03*(g[:,None]*pu-.001*qi))
            np.add.at(Q, jn, .03*(-g[:,None]*pu-.001*qj))

    return P, Q, eligible


def operational(d):
    """Lọc phiên có năng lượng, duration dương và tính các tỷ lệ theo kWh."""
    x = d.copy()
    x['duration'] = (x.end-x.start).dt.total_seconds()/60
    x = x[(x['Transaction power/kwh'] > 0) & (x.duration > 0)].copy()
    x['cost_rate'] = x['Actual Payment/Yuan']/x['Transaction power/kwh']
    x['gross_rate'] = x['Transaction Amount/Yuan']/x['Transaction power/kwh']
    x['minutes_rate'] = x.duration/x['Transaction power/kwh']
    return x

def scale(x):
    """Chuẩn hóa min–max theo trục cuối; biến hằng được ánh xạ về không."""
    low = np.min(x, axis=-1, keepdims=True)
    span = np.max(x, axis=-1, keepdims=True)-low
    return np.divide(x-low, span, out=np.zeros_like(x, dtype=float), where=span>0)

def main():
    """Chạy toàn bộ pilot validation và ghi kết quả có thể tái lập.

    SEED và số chiều đọc từ biến môi trường; test chỉ được thống kê độ phủ.
    """
    OUT.mkdir(exist_ok=True)
    SEED = int(os.environ.get('JIAXING_PILOT_SEED', '20261120'))
    DIM = int(os.environ.get('JIAXING_PILOT_DIM', '8'))
    cohort = os.environ.get('JIAXING_PILOT_COHORT', 'all')
    if cohort not in {'all', 'positive_energy', 'positive_energy_nonabnormal'}:
        raise ValueError(f'Cohort không hợp lệ: {cohort}')
    rng = np.random.default_rng(SEED)
    df = load_transactions(ROOT / '28182251/Dataset/Charging_Data.csv')
    raw_events = len(df)
    if cohort != 'all':
        df = df[df['Transaction power/kwh'] > 0].copy()
    if cohort == 'positive_energy_nonabnormal':
        df = df[df['is_abnormal'] == 0].copy()
    train = df[df.start < '2021-07-01'].copy()
    val = df[(df.start >= '2021-07-01') & (df.start < '2021-10-01')].copy()
    test = df[df.start >= '2021-10-01'].copy()
    sites = sorted(train.site.unique())
    site_to_id = {s: i for i, s in enumerate(sites)}
    users = sorted(train.UserID.unique())
    user_to_id = {u: i for i, u in enumerate(users)}
    n, m = len(users), len(sites)
    counts = np.zeros((n, m), dtype=np.int32)
    edges = train.groupby(['UserID', 'site']).size()
    for (u, site), count in edges.items():
        counts[user_to_id[u], site_to_id[site]] = count
    pop = counts.sum(axis=0).astype(float)
    pop_users = (counts > 0).sum(axis=0).astype(float)

    def query_stats(part):
        """Chọn lượt đầu mỗi user và đếm warm, cold, lượt ghé lại và mới."""
        q = part.drop_duplicates('UserID', keep='first').copy()
        q['warm'] = q.UserID.isin(user_to_id)
        q['known_site'] = q.site.isin(site_to_id)
        warm = q[q.warm & q.known_site]
        rep = sum(counts[user_to_id[u], site_to_id[s]] > 0 for u, s in zip(warm.UserID, warm.site))
        return q, {'first_query_users': len(q), 'warm_users': int(q.warm.sum()),
                   'cold_users': int((~q.warm).sum()), 'unknown_target_site': int((~q.known_site).sum()),
                   'warm_repeat_target': int(rep), 'warm_new_target': len(warm)-int(rep)}

    vq, vaudit = query_stats(val)
    _, taudit = query_stats(test)
    evalq = vq[vq.warm & vq.known_site]
    ui = np.array([user_to_id[x] for x in evalq.UserID])
    target = np.array([site_to_id[x] for x in evalq.site])

    P, Q, eligible = train_bpr(counts, DIM, rng)

    scores = P[ui] @ Q.T
    popscore = np.broadcast_to(pop, scores.shape)
    userscore = np.broadcast_to(pop_users, scores.shape)
    personal = counts[ui].astype(float) + (pop / (pop.max()+1)) * 1e-6

    def evaluate(score):
        """Tính Hit Rate và NDCG với một mục tiêu cho mỗi truy vấn warm."""
        order = np.argsort(-score, axis=1, kind='stable')
        ranks = np.argmax(order == target[:,None], axis=1) + 1
        return {str(k): {'hit_rate': float(np.mean(ranks <= k)),
                         'ndcg': float(np.mean(np.where(ranks <= k, 1/np.log2(ranks+1), 0)))}
                for k in [1, 3, 5]}

    all_operational, ov = operational(train), operational(val)
    cutoff = pd.Timestamp('2021-07-01')
    # End is needed for duration and delivered energy. Payment timestamp is
    # only a conservative proxy for cost availability, not verified semantics.
    duration_train = all_operational[all_operational.end < cutoff].copy()
    payment_train = duration_train[duration_train.payment_time < cutoff].copy()
    duration_agg = duration_train.groupby('site').agg(duration_n=('minutes_rate','size'), time=('minutes_rate','median'))
    cost_agg = payment_train.groupby('site').agg(n=('cost_rate','size'), cost=('cost_rate','median'),
                                                  gross=('gross_rate','median'))
    agg = cost_agg.join(duration_agg, how='outer').reindex(sites)
    if not ((agg.n >= 30) & (agg.duration_n >= 30)).all():
        raise ValueError('Ít nhất một site thiếu 30 phiên train cho cost hoặc duration; cần định nghĩa fallback.')
    c, d = 20 * agg.cost.to_numpy(), 20 * agg.time.to_numpy()
    valid = ov[ov.site.isin(sites)].copy()
    valid['pred_cost'] = valid.site.map(agg.cost) * valid['Transaction power/kwh']
    valid['pred_time'] = valid.site.map(agg.time) * valid['Transaction power/kwh']
    errc = np.abs(valid.pred_cost-valid['Actual Payment/Yuan'])
    errt = np.abs(valid.pred_time-valid.duration)

    # Query-local relevance min-max is an explicit pilot design; operational scales
    # use train-derived site estimates. Constant dimensions are mapped to zero.
    zr, zc, zd = scale(scores), scale(c), scale(d)
    weighted = .5*zr - .25*zc - .25*zd

    def front_order(r):
        """Xếp Pareto front, rồi relevance giảm dần và site key ổn định."""
        objs = np.column_stack([-r, c, d])
        dominates = (objs[:,None,:] <= objs[None,:,:]).all(axis=2) & (objs[:,None,:] < objs[None,:,:]).any(axis=2)
        remaining = np.ones(m, bool)
        layers = []
        while remaining.any():
            front = remaining & ~(dominates & remaining[:,None]).any(axis=0)
            layer = np.flatnonzero(front)
            layers.extend(sorted(layer, key=lambda i: (-r[i], i)))
            remaining[front] = False
        return np.array(layers)

    orders = np.vstack([front_order(r) for r in scores])
    pareto_score = np.empty_like(scores)
    np.put_along_axis(pareto_score, orders, np.broadcast_to(np.arange(m,0,-1), orders.shape), axis=1)

    methods = {'popularity': popscore, 'popularity_distinct_users': userscore, 'personal_frequency': personal, 'bpr_mf': scores,
               'weighted_sum': weighted, 'pareto_front_relevance': pareto_score}
    # Greedy relevance/diversity selection: dissimilarity is defined ONLY by
    # estimated train-site cost and duration; it is not geographic diversity.
    dissimilarity = (np.abs(zc[:,None]-zc[None,:]) + np.abs(zd[:,None]-zd[None,:])) / 2
    def diverse_order(relevance, alpha):
        """Chọn lần lượt theo relevance và độ khác biệt trung bình với danh sách."""
        available = np.ones(m, dtype=bool)
        ordered = []
        for _ in range(m):
            diversity = dissimilarity[:, ordered].mean(axis=1) if ordered else np.zeros(m)
            value = alpha*relevance + (1-alpha)*diversity
            value[~available] = -np.inf
            chosen = int(np.argmax(value))
            ordered.append(chosen)
            available[chosen] = False
        return np.array(ordered)
    for alpha in [.5, .8]:
        greedy_orders = np.vstack([diverse_order(row, alpha) for row in zr])
        greedy_score = np.empty_like(scores)
        np.put_along_axis(greedy_score, greedy_orders, np.broadcast_to(np.arange(m,0,-1), greedy_orders.shape), axis=1)
        methods[f'diversity_greedy_alpha_{alpha}'] = greedy_score
    result = {'scope': 'exploratory validation; one first query per user; train frozen; test metrics not evaluated',
              'interaction_cohort': cohort, 'raw_events': raw_events, 'cohort_events': len(df),
              'split': {'train_before':'2021-07-01','validation_before':'2021-10-01',
                        'train_events':len(train),'validation_events':len(val),'test_events':len(test),
                        'train_users':n,'sites_in_training':m,'validation_users':vaudit,'test_users':taudit},
              'seed':SEED,'latent_dimensions':DIM,'trainable_users':len(eligible),'methods':{},
              'availability_policy': {'duration':'positive energy and duration, end strictly before cutoff',
                                      'payment_and_gross':'duration rule and payment timestamp strictly before cutoff; proxy not verified'},
              'estimator_validation': {'positive_energy_duration_train':len(all_operational), 'duration_train_available':len(duration_train),
                                       'payment_train_proxy_available':len(payment_train),
                                       'positive_energy_duration_validation':len(valid),
                                       'train_site_samples_min':int(agg.n.min()),'duration_site_samples_min':int(agg.duration_n.min()),
                                       'actual_payment_mae_cny':float(errc.mean()),
                                       'duration_mae_min':float(errt.mean()),'actual_payment_median_absolute_error_cny':float(errc.median()),
                                       'duration_median_absolute_error_min':float(errt.median()),
                                       'predicted_20kwh_cost_range_cny':[float(c.min()),float(c.max())],
                                       'predicted_20kwh_duration_range_min':[float(d.min()),float(d.max())]}}
    for name, score in methods.items():
        top = np.argmax(score, axis=1)
        order3 = np.argsort(-score, axis=1, kind='stable')[:, :3]
        pair_distance = (dissimilarity[order3[:,0],order3[:,1]] + dissimilarity[order3[:,0],order3[:,2]] +
                         dissimilarity[order3[:,1],order3[:,2]]) / 3
        result['methods'][name] = {'ranking':evaluate(score), 'estimated_top1_cost_cny':float(c[top].mean()),
                                   'estimated_top1_duration_min':float(d[top].mean()),
                                   'operational_ild_at_3':float(pair_distance.mean()),
                                   'catalog_coverage_at_3':float(len(np.unique(order3))/m)}
    coldq = vq[(~vq.warm) & vq.known_site]
    cold_target = np.array([site_to_id[x] for x in coldq.site])
    pop_order = np.argsort(-pop, kind='stable')
    cold_ranks = np.argmax(pop_order[None,:] == cold_target[:,None], axis=1) + 1
    result['cold_user_popularity_fallback'] = {
        'users': len(coldq),
        'ranking': {str(k): {'hit_rate': float(np.mean(cold_ranks <= k)),
                             'ndcg': float(np.mean(np.where(cold_ranks <= k, 1/np.log2(cold_ranks+1), 0)))}
                    for k in [1, 3, 5]}}
    history = counts[ui].sum(axis=1)
    result['warm_history_group_sizes'] = {'one_train_visit':int((history == 1).sum()),
                                          'two_to_four_train_visits':int(((history >= 2)&(history <= 4)).sum()),
                                          'five_or_more_train_visits':int((history >= 5).sum())}
    result['warm_history_group_metrics'] = {}
    for group, mask in [('one_train_visit', history == 1),
                        ('two_to_four_train_visits', (history >= 2) & (history <= 4)),
                        ('five_or_more_train_visits', history >= 5)]:
        group_result = {'users': int(mask.sum())}
        for name, score in methods.items():
            order = np.argsort(-score[mask], axis=1, kind='stable')
            ranks = np.argmax(order == target[mask,None], axis=1) + 1
            group_result[name] = {'hit_rate_at_3': float(np.mean(ranks <= 3)),
                                  'ndcg_at_3': float(np.mean(np.where(ranks <= 3, 1/np.log2(ranks+1), 0)))}
        result['warm_history_group_metrics'][group] = group_result

    # Paired user bootstrap for the difference in NDCG@3, one query per user.
    def ndcg3(score):
        """Trả NDCG@3 theo từng người dùng, phục vụ so sánh ghép cặp."""
        order = np.argsort(-score, axis=1, kind='stable')
        ranks = np.argmax(order == target[:,None], axis=1) + 1
        return np.where(ranks <= 3, 1/np.log2(ranks+1), 0)
    def ild3(score, distances):
        """Trả diversity trung bình của ba cặp trong Top-3 của từng người dùng."""
        order = np.argsort(-score, axis=1, kind='stable')[:, :3]
        return (distances[order[:,0],order[:,1]] + distances[order[:,0],order[:,2]] +
                distances[order[:,1],order[:,2]]) / 3
    bootstrap_rng = np.random.default_rng(8821)
    result['paired_ndcg3_differences'] = {}
    for a, b in [('bpr_mf', 'personal_frequency'), ('weighted_sum', 'bpr_mf'),
                 ('pareto_front_relevance', 'bpr_mf'),
                 ('diversity_greedy_alpha_0.5','bpr_mf'), ('diversity_greedy_alpha_0.8','bpr_mf')]:
        diff = ndcg3(methods[a]) - ndcg3(methods[b])
        boot = np.array([diff[bootstrap_rng.integers(0, len(diff), len(diff))].mean() for _ in range(1000)])
        result['paired_ndcg3_differences'][f'{a}_minus_{b}'] = {
            'mean': float(diff.mean()), 'bootstrap_95_percentile_ci': np.quantile(boot, [.025,.975]).tolist()}
    result['paired_ild3_differences'] = {}
    for a in ['weighted_sum','pareto_front_relevance','diversity_greedy_alpha_0.5','diversity_greedy_alpha_0.8']:
        diff = ild3(methods[a], dissimilarity)-ild3(methods['bpr_mf'], dissimilarity)
        boot = np.array([diff[bootstrap_rng.integers(0,len(diff),len(diff))].mean() for _ in range(1000)])
        result['paired_ild3_differences'][f'{a}_minus_bpr_mf'] = {
            'mean':float(diff.mean()), 'bootstrap_95_percentile_ci':np.quantile(boot,[.025,.975]).tolist()}

    energy = valid['Transaction power/kwh']
    global_cost = float(payment_train.cost_rate.median())
    global_gross = float(payment_train.gross_rate.median())
    global_time = float(duration_train.minutes_rate.median())
    gross_err = np.abs(valid.site.map(agg.gross)*energy-valid['Transaction Amount/Yuan'])
    result['estimator_validation']['global_actual_payment_mae_cny'] = float(np.abs(global_cost*energy-valid['Actual Payment/Yuan']).mean())
    result['estimator_validation']['global_duration_mae_min'] = float(np.abs(global_time*energy-valid.duration).mean())
    result['estimator_validation']['site_gross_amount_mae_cny'] = float(gross_err.mean())
    result['estimator_validation']['global_gross_amount_mae_cny'] = float(np.abs(global_gross*energy-valid['Transaction Amount/Yuan']).mean())
    result['weight_sensitivity'] = {}
    for label, (wr, wc, wd) in {'balanced':(.5,.25,.25), 'cost_focused':(.3,.5,.2),
                                'duration_focused':(.3,.2,.5), 'relevance_focused':(.8,.1,.1)}.items():
        candidate_score = wr*zr-wc*zc-wd*zd
        top = np.argmax(candidate_score, axis=1)
        result['weight_sensitivity'][label] = {'weights':[wr,wc,wd], 'ranking':evaluate(candidate_score),
            'estimated_top1_cost_cny':float(c[top].mean()), 'estimated_top1_duration_min':float(d[top].mean())}
    gross_c = 20 * agg.gross.to_numpy()
    zgross = scale(gross_c)
    gross_distance = (np.abs(zgross[:,None]-zgross[None,:]) + np.abs(zd[:,None]-zd[None,:])) / 2
    result['diversity_metric_gross_sensitivity'] = {
        name:float(ild3(score,gross_distance).mean()) for name,score in methods.items()}
    result['exposure_at_3'] = {}
    for name, score in methods.items():
        order = np.argsort(-score,axis=1,kind='stable')[:,:3]
        visits = np.bincount(order.ravel(),minlength=m)
        shares = visits / visits.sum()
        result['exposure_at_3'][name] = {'top_site_share':float(shares.max()),
            'top_3_sites_share':float(np.sort(shares)[-3:].sum()), 'site_shares':dict(zip(sites,shares.tolist()))}
    gross_score = .5*zr-.25*scale(gross_c)-.25*zd
    gross_top = np.argmax(gross_score,axis=1)
    result['gross_cost_sensitivity'] = {'ranking':evaluate(gross_score),
        'estimated_top1_gross_cny':float(gross_c[gross_top].mean()),
        'estimated_top1_duration_min':float(d[gross_top].mean()),
        'top1_changed_fraction_vs_actual_payment':float(np.mean(gross_top != np.argmax(weighted,axis=1)))}
    valid['cost_abs_error'] = errc
    valid['duration_abs_error'] = errt
    valid['gross_abs_error'] = gross_err
    site_errors = valid.groupby('site').agg(validation_sessions=('duration','size'),
        cost_mae_cny=('cost_abs_error','mean'), duration_mae_min=('duration_abs_error','mean'),
        gross_mae_cny=('gross_abs_error','mean'))
    suffix = '_availability_proxy' + ('' if cohort == 'all' else f'_cohort_{cohort}')
    site_errors.to_csv(OUT/f'validation_site_errors{suffix}.csv')
    agg.assign(estimated_20kwh_cost=c, estimated_20kwh_duration=d).to_csv(OUT/f'station_estimates{suffix}.csv')
    quarterly_cost = payment_train.assign(quarter=payment_train['start'].dt.to_period('Q').astype(str)).groupby(['site','quarter']).agg(
        sessions=('cost_rate','size'), actual_cost_per_kwh=('cost_rate','median'),
        gross_cost_per_kwh=('gross_rate','median'))
    quarterly_time = duration_train.assign(quarter=duration_train['start'].dt.to_period('Q').astype(str)).groupby(['site','quarter']).agg(
        duration_sessions=('minutes_rate','size'), minutes_per_kwh=('minutes_rate','median'))
    quarterly = quarterly_cost.join(quarterly_time, how='outer')
    quarterly.to_csv(OUT/f'training_site_quarterly_rates{suffix}.csv')
    (OUT/f'results_dim_{DIM}_seed_{SEED}{suffix}.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
