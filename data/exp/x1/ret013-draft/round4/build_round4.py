"""Round 4 drafts (Ronin agent / model, 2026-10-07, NOT human-reviewed). Offline, no API. Writes only under round4/ and /tmp/x1-ronin/round4/.
Run: X1_OUT=/workspace/x1-labeling/v2/drafts env -u DASHSCOPE_API_KEY /workspace/venv-fl/bin/python build_round4.py"""
import sys, json, re, shutil, difflib, collections, copy
from pathlib import Path
sys.path.insert(0, '/workspace/x1-labeling/v4'); sys.path.insert(0, '/workspace/x1-labeling/ronin-review/round4/part2')
from load import *
import rules_v4 as R
from units import U
RR = Path('/workspace/x1-labeling/ronin-review'); R4 = RR / 'round4'; TMP = Path('/tmp/x1-ronin/round4')
V2 = Path('/workspace/x1-labeling/v2/drafts'); PUB = Path('/workspace/x1-run/data/exp/x1/corpus')
AUTH = 'Ronin 代理人（模型）起草，2026-10-07，未经人工审核'
FINAL = json.load(open(RR / 'final/questions.final.json'))
QS = copy.deepcopy(FINAL['queries'])

# ---------------- combined corpus copies (base and round4) ----------------
def build_combined(dst, patch_memo=False, new_docs=()):
    if dst.exists(): shutil.rmtree(dst)
    for sub in ('corpus', 'traps'): shutil.copytree(V2 / sub, dst / sub)
    for snap in ('t0', 't1'):
        for p in (PUB / snap).glob('*.md'): shutil.copy(p, dst / 'corpus' / snap / p.name)
    if patch_memo: (dst / 'corpus/t1/s6-d2-g2-memo.md').write_text(MEMO_NEW)
    for snap, name, text in new_docs: (dst / 'corpus' / snap / name).write_text(text)
    return dst

# ---------------- 1. category-rule-v2 ----------------
sys.path.insert(0, str(RR / 'work/item5'))
K2_SYN = {k: v for k, v in __import__('recategorize').K2_SYN.items()}   # same judgments as TRAP-DEFINITIONS-draft §5 (D5 counted)
def category_v2(q, new_kind=None):
    """category-rule-v2 (owner D2=甲 2026-10-07 13:16). Order: K1 guardrail -> K2 statute pair / conflict_pair -> K2 judged synthetic ->
    K3 meta lure (judged) -> adversarial (query-side) -> hard. Returns (category, kind, reason)."""
    if q['score_role'] == 'guardrail': return 'trap', 'K1', '快照取代：护栏题（T0 旧版在 distractors），不进分母'
    if new_kind: return 'trap', new_kind[0], new_kind[1]
    Rr = {e.split('@')[0] for e in q['relevant'] if e.endswith('@' + q['as_of'])}; D = {e.split('@')[0] for e in q['distractors'] if e.endswith('@' + q['as_of'])}
    if q.get('conflict_pair'): return 'trap', 'K2', '同快照冲突：conflict_pair'
    for k, (old, new) in R.CPAIRS.items():
        if (Rr & (old | new)) and (Rr | D) & old and (Rr | D) & new: return 'trap', 'K2', f'同快照冲突：条文对 {k}，新旧两侧都在 relevant∪distractors（D3: s6-d1-c4-q1 计 trap）'
    if q['id'] in K2_SYN: return 'trap', 'K2', '同快照冲突（逐题判定' + ('，D5 边界暂计入' if K2_SYN[q['id']][0] == 'borderline' else '') + '）：' + K2_SYN[q['id']][1]
    return 'hard', '-', 'K1–K3 不成立；问句无对抗改写（D4: s7-d3-t1-05-q3 → hard）'
cmp_rows = []
for q in QS:
    old = q['category']; new, kind, why = category_v2(q)
    q['category'] = new; q['category_rule'] = 'category-rule-v2-draft'; q['trap_kind'] = kind
    cmp_rows.append(dict(id=q['id'], score_role=q['score_role'], old=old, new=new, kind=kind, changed=old != new, reason=why))
arm = [q for q in QS if q['score_role'] == 'arm']; nta = sum(q['category'] in ('trap', 'adversarial') for q in arm)
cat_sum = dict(n_arm=len(arm), trap_adv=nta, ratio=round(nta / len(arm) * 100, 2), need=-(-3 * len(arm) // 10),
               changed=[(r['id'], r['old'], r['new']) for r in cmp_rows if r['changed']])
d = R4 / 'category-rule-v2'
json.dump(dict(meta=dict(FINAL.get('meta', {}), category_rule='category-rule-v2-draft', drafted_by=AUTH), queries=QS), open(d / 'questions.category-v2.json', 'w'), ensure_ascii=False, indent=1)
with open(d / 'category-compare.tsv', 'w') as fh:
    fh.write('id\tscore_role\told\tnew\tkind\tchanged\treason\n')
    for r in cmp_rows: fh.write('\t'.join(str(r[k]) for k in ('id', 'score_role', 'old', 'new', 'kind', 'changed', 'reason')) + '\n')
json.dump(cat_sum, open(d / 'summary.json', 'w'), ensure_ascii=False, indent=1)

# ---------------- 2. s6-d2-g2-q1 option A ----------------
MEMO_OLD = (V2 / 'corpus/t1/s6-d2-g2-memo.md').read_text()
OLD_S = '旧法（2018修正）的施行日期为二〇〇六年一月一日。'
NEW_S = '旧法（2018修正）自二〇一八年十月二十六日起施行。'
assert MEMO_OLD.count(OLD_S) == 1
MEMO_NEW = MEMO_OLD.replace(OLD_S, NEW_S)
dA = R4 / 's6-d2-g2-A'
(dA / 's6-d2-g2-memo.md').write_text(MEMO_NEW)
(dA / 's6-d2-g2-memo.md.diff').write_text(''.join(difflib.unified_diff(MEMO_OLD.splitlines(True), MEMO_NEW.splitlines(True), 'v2/drafts/corpus/t1/s6-d2-g2-memo.md', 'round4/s6-d2-g2-A/s6-d2-g2-memo.md')))
qA = next(q for q in QS if q['id'] == 's6-d2-g2-q1'); qA_old = copy.deepcopy(next(q for q in FINAL['queries'] if q['id'] == 's6-d2-g2-q1'))
qA['query'] = '新公司法（2023修订）的施行日期是什么？其第二百六十六条对出资期限有何要求？'
qA['answer_points'] = [a for a in qA['answer_points'] if '二〇〇六' not in a]
# apply memo patch to in-memory chunks, then recheck APs and qtype
for doc, cs in load_corpus(build_combined(TMP / 'memo-only', patch_memo=True) / 'corpus'):
    for c in cs:
        if c.doc_id == 's6-d2-g2-memo': C[chunk_evidence_id(c)]['text'] = c.text
qtA, whyA = R.qtype_kw(qA['query'], 'arm', qA['relevant'], qA['answer_points']); qA['qtype'] = qtA
apA = {a: any(xc.clean_text(a) in body(e) for e in qA['relevant']) for a in qA['answer_points']}
# other questions citing the memo chunk: APs still substrings?
memo_users = [(q['id'], a, any(xc.clean_text(a) in body(e) for e in q['relevant'])) for q in QS for a in q['answer_points'] if any(e.startswith('s6-d2-g2-memo#') for e in q['relevant'])]
json.dump(dict(before=qA_old, after=qA), open(dA / 's6-d2-g2-q1.before-after.json', 'w'), ensure_ascii=False, indent=1)
(dA / 's6-d2-g2-q1.diff').write_text(''.join(difflib.unified_diff(json.dumps(qA_old, ensure_ascii=False, indent=1).splitlines(True), json.dumps({k: qA[k] for k in qA_old}, ensure_ascii=False, indent=1).splitlines(True), 'final/questions.final.json#s6-d2-g2-q1', 'round4 draft')))
A_sum = dict(memo_sentence_old=OLD_S, memo_sentence_new=NEW_S, flk_2018_amendment_effective='2018-10-26（flk 详情 ff8080816f135f46016f1cc98ad81134，见 SOURCES-revision-check.md 第1行）',
             q_qtype_before=qA_old['qtype'], q_qtype_after=qtA, q_qtype_reason=whyA, ap_substring_ok=apA, all_memo_ap_users=memo_users)
json.dump(A_sum, open(dA / 'check.json', 'w'), ensure_ascii=False, indent=1)

# ---------------- 3. part 1: mined from existing corpus ----------------
P1 = [
 dict(id='r4m-s5-d3-t1-05-q4', as_of='T1', query='按官方最新统计，这个地区的制造业在经济总量里还占三成以上吗？',
      relevant=['s5-d3-t1-05-report#p2@T1'], answer_points=['该比例已下降至28%'], distractors=['s5-d3-t1-05-report#p1@T1', 's5-d3-t1-05-report#p3@T1'],
      kind=('K2', '同快照冲突：report#p1「制造业产值占GDP比重为34%」(2021白皮书，仍被引用) 与 report#p2「已下降至28%」(2023官方更新) 同在 T1；旧值在 distractors，答 34% 即错')),
 dict(id='r4m-s5-d3-t1-05-q5', as_of='T1', query='员工对工作环境满不满意，最新一轮调查给出的比例是多少？',
      relevant=['s5-d3-t1-05-analysis#p2@T1'], answer_points=['满意度已升至67%'], distractors=['s5-d3-t1-05-analysis#p1@T1', 's5-d3-t1-05-analysis#p3@T1'],
      kind=('K2', '同快照冲突：analysis#p1「仅有39%满意」(2020) 与 analysis#p2「已升至67%」(2023) 同在 T1；旧值在 distractors')),
 dict(id='r4m-s5-d3-t1-05-q6', as_of='T1', query='城市居民每天坐公交出行的人，最近那次独立调查测出来占多少？',
      relevant=['s5-d3-t1-05-memo#p2@T1'], answer_points=['使用公共交通的比例上升至51%'], distractors=['s5-d3-t1-05-memo#p1@T1', 's5-d3-t1-05-memo#p3@T1'],
      kind=('K2', '同快照冲突：memo#p1「约43%」(2022，仍被频繁引用) 与 memo#p2「上升至51%」(2023) 同在 T1；旧值在 distractors。注意：与 s5-d3-t1-05-q1（问变化，两侧都相关）题意相近，owner 可删'), near_dup='s5-d3-t1-05-q1'),
 dict(id='r4m-s5-d0-t1-02-q5', as_of='T1', query='被媒体反复转述的早高峰车速和拥堵时长，独立研究实际测到的是多少？',
      relevant=['s5-d0-t1-02-memo#p2@T1'], answer_points=['真实车速为16公里/小时', '拥堵时长约为3.2小时'], distractors=['s5-d0-t1-02-memo#p1@T1', 's5-d0-t1-02-memo#p3@T1'],
      kind=('K2', '同快照冲突：memo#p1 转述值「12公里/小时、超过4.5小时」与 memo#p2 复现实测「16公里/小时、约3.2小时」同在 T1；转述值在 distractors')),
 dict(id='r4m-s3-d3-01-q5', as_of='T1', query='竞品B这一期的月费，两份比价材料写得一样吗？各写了多少？',
      relevant=['s3-d3-01-memo#p2@T1', 's3-d3-01-report#p2@T1'], answer_points=['月费降至129元', '月费最低可至99元'], distractors=['s3-d3-01-memo#p1@T1', 's3-d3-01-memo#p3@T1'],
      kind=('K2', '同快照冲突（问两侧）：memo#p2「限时优惠129元」与 report#p2「按需计费最低99元」同一 T1 快照对竞品B月费说法不一，两侧都在 relevant')),
 dict(id='r4m-s3-d0-02-q7', as_of='T1', query='C公司149元的新方案现在已经开卖了吗？两份比价材料怎么说？',
      relevant=['s3-d0-02-a#p3@T1', 's3-d0-02-b#p3@T1'], answer_points=['正式版本将于下季度以149元起售', '改推“成长计划”订阅制，首年费用149元', '用户迁移率已达72%'], distractors=['s3-d0-02-c#p3@T1', 's3-d0-02-a#p2@T1'],
      kind=('K2', '同快照冲突（问两侧）：a#p3 说暂停注册、149元正式版「将于下季度」起售；b#p3 说已改推149元订阅、迁移率已达72%。同一 T1 快照对是否已上市矛盾，两侧都在 relevant')),
]

# ---------------- 4. part 2: new corpus docs + questions ----------------
NEW_DOCS = []; P2 = []
GTYPE = {'S1': '顾问备忘', 'S2': '访谈/渠道纪要', 'S3': '竞品价目', 'S4': '内部测算', 'S5': '二手转述/汇编', 'S6': '变更要点'}
for u in U:
    snap = u['as_of'].lower()
    for (dn, title), cs, st in ((u['d1'], u['c1'], 'private'), (u['d2'], u['c2'], 'internal')):
        doc_id = f"{u['b']}-{dn}"
        text = f"---\ndoc_id: {doc_id}\nas_of: {u['as_of']}\nsource_type: {st}\ntitle: {title}\nprovenance: synthetic\nlicense: synthetic\ndomain: {u['dom']}\ngenre: {u['genre']}\n---\n" + ''.join(f'## p{i+1}\n{c}\n' for i, c in enumerate(cs))
        NEW_DOCS.append((snap, doc_id + '.md', text))
    a = u['as_of']; d1 = f"{u['b']}-{u['d1'][0]}"; d2 = f"{u['b']}-{u['d2'][0]}"
    e = lambda doc, p: f'{doc}#p{p}@{a}'
    P2 += [
     dict(id=f"r4n-{u['b']}-qa", as_of=a, query=u['qa'], relevant=[e(d2, 1)], answer_points=u['apa'], distractors=[e(d1, 1), e(d2, 3)],
          kind=('K2', f'同快照冲突：{d1}#p1 给旧/错误值，{d2}#p1 给现行值并说明依据；错误一侧在 distractors')),
     dict(id=f"r4n-{u['b']}-qb", as_of=a, query=u['qb'], relevant=[e(d1, 1), e(d2, 1)], answer_points=u['apb'], distractors=[e(d1, 3), e(d2, 3)],
          kind=('K2', f'同快照冲突（问两侧）：{d1}#p1 与 {d2}#p1 对同一对象说法矛盾，两侧都在 relevant')),
     dict(id=f"r4n-{u['b']}-qc", as_of=a, query=u['qc'], relevant=[e(d2, 2)], answer_points=u['apc'], distractors=[e(d1, 2), e(d1, 3)],
          kind=('K3', f'元陈述：{d1}#p2 只说该指标未复测/无新数据/待发布/未入账/不再列入跟踪，不含数值，却与问句同词；实测值在 {d2}#p2')),
    ]
CB = build_combined(TMP / 'combined-r4', patch_memo=True, new_docs=NEW_DOCS)
for snap, name, _ in NEW_DOCS:
    pass
for doc, cs in load_corpus(CB / 'corpus'):
    for c in cs:
        eid = chunk_evidence_id(c)
        if eid not in C: C[eid] = dict(eid=eid, doc_id=c.doc_id, clause=c.clause_id, as_of=c.as_of, text=c.text, kind='syn-r4', title='')
for snap, name, text in NEW_DOCS: (R4 / 'part2/corpus' / snap).mkdir(parents=True, exist_ok=True); (R4 / 'part2/corpus' / snap / name).write_text(text)

def finish(q):
    q.update(score_role='arm', eval_intent='draft-r4: ' + q['kind'][1][:60], drafted_by=AUTH)
    q['qtype'], q['qtype_reason'] = R.qtype_kw(q['query'], 'arm', q['relevant'], q['answer_points'])
    q['category'], q['trap_kind'], q['trap_mechanism'] = category_v2(q, q.pop('kind'))
    rc = [body(x) for x in q['relevant']]; cq = xc.strip_law_names(xc.clean_text(q['query']))
    q['self_check'] = dict(r8=round(xc.eight_gram_overlap(cq, rc) or 0, 3), lcs=round(xc.lcs_ratio(cq, rc) or 0, 3),
        ap_substring=all(any(xc.clean_text(a) in b for b in rc) for a in q['answer_points']),
        ids_exist=all(x in C for x in q['relevant'] + q['distractors']), same_snapshot=all(x.endswith('@' + q['as_of']) for x in q['relevant'] + q['distractors']),
        no_overlap=not (set(q['relevant']) & set(q['distractors'])))
    s = q['self_check']; s['pass'] = s['ap_substring'] and s['ids_exist'] and s['same_snapshot'] and s['no_overlap'] and (q['qtype'] == 'lexical' or (s['r8'] <= 0.2 and s['lcs'] < 0.8))
    return q
P1 = [finish(q) for q in P1]; P2 = [finish(q) for q in P2]
json.dump(dict(meta=dict(drafted_by=AUTH, note='只用现有语料；需 owner 审后按协议双标'), queries=P1), open(R4 / 'part1/questions.part1.json', 'w'), ensure_ascii=False, indent=1)
json.dump(dict(meta=dict(drafted_by=AUTH, note='需 owner 授权并入 v2/drafts 后按协议双标（A + B 盲标）'), queries=P2), open(R4 / 'part2/questions.part2.json', 'w'), ensure_ascii=False, indent=1)

# ---------------- gap math + full check_x1 on the projected set ----------------
base_trap = nta; base_n = len(arm); m = len(P1)
x_min = next(x for x in range(0, 500) if (base_trap + x) / (base_n + x) >= 0.30)
need_new = x_min + 3 - m
ALL = QS + P1 + P2
def to_check(q):
    o = {k: q[k] for k in ('id', 'query', 'category', 'as_of', 'relevant', 'answer_points', 'distractors', 'qtype', 'score_role')}
    o['eval_intent'] = q.get('eval_intent') or 'draft'
    if q.get('conflict_pair'): o['conflict_pair'] = q['conflict_pair']
    return o
cfg = json.load(open('/workspace/x1-run/data/exp/x1/config.json')); (TMP / 'config.json').write_text(json.dumps(cfg))
res = {}
for name, qs, cbdir in (('base_final', FINAL['queries'], build_combined(TMP / 'combined-base')), ('v2_only', QS, CB), ('projected', ALL, CB)):
    p = TMP / f'questions-{name}.json'; p.write_text(json.dumps(dict(queries=[to_check(q) for q in qs]), ensure_ascii=False))
    r = xc.check_x1(str(cbdir / 'corpus'), str(cbdir / 'traps'), p, str(TMP / 'config.json'))
    a_ = [q for q in qs if q['score_role'] == 'arm']; t_ = sum(q['category'] in ('trap', 'adversarial') for q in a_)
    res[name] = dict(exit=r.exit_code, qtype_arm=r.qtype_counts, n_arm=r.n_arm, n_guardrail=r.n_guardrail, trap_adv=t_, ratio=round(r.trap_adversarial_ratio * 100, 2),
                     need=-(-3 * len(a_) // 10), slack=t_ - -(-3 * len(a_) // 10), chunks=r.n_chunks, syn=round(r.synthetic_ratio, 4), decontam=r.decontam_hits, lcs_flags=r.lcs_flags,
                     license=r.license_violations, messages=r.messages[:30])
S = dict(category_v2=cat_sum, s6_d2_g2_A=dict(qtype=[qA_old['qtype'], qtA], ap_ok=apA, memo_users_ok=all(x[2] for x in memo_users)),
         part1=dict(n=m, qtype=dict(collections.Counter(q['qtype'] for q in P1)), kinds=dict(collections.Counter(q['trap_kind'] for q in P1)), fail=[q['id'] for q in P1 if not q['self_check']['pass']]),
         gap=dict(base_trap=base_trap, base_arm=base_n, x_min_total_new=x_min, plus_margin=x_min + 3, mined=m, need_new_written=need_new, drafted=len(P2)),
         part2=dict(n=len(P2), docs=len(NEW_DOCS), chunks=3 * len(NEW_DOCS), qtype=dict(collections.Counter(q['qtype'] for q in P2)), kinds=dict(collections.Counter(q['trap_kind'] for q in P2)),
                    batches=len(U), genres=dict(collections.Counter(u['genre'] for u in U)), snaps=dict(collections.Counter(u['as_of'] for u in U)), fail=[q['id'] for q in P2 if not q['self_check']['pass']]),
         check=res)
json.dump(S, open(R4 / 'build-summary.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in S.items() if k != 'category_v2'}, ensure_ascii=False, indent=1)[:6000]); print(cat_sum['trap_adv'], cat_sum['ratio'], len(cat_sum['changed']))
