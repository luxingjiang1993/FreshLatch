# 公开可复现 eval 包（A-P7）

公开可复现 ≠ 登上权威榜。

本页说明固定 eval 包的本地回放。层是 smoke。`counted_as_pass` 恒为 false。本包不发明 SESOI，不改 floors、gold、x1、`PRODUCTION_RETRIEVAL_MODE`，不重跑 C-04，不改 RESULT-Y。复现结果保持在这条冒烟回放里。

代码：`src/freshlatch/eval/public_pack.py`。夹具：`tests/eval/fixtures/a_p7_public_eval_pack.json`。

## 回放命令

```bash
python -m freshlatch.eval public-pack
```

stdout 是 RESULT JSON，字段 `content_hash` 为 64 位小写 hex。

核对同一份 RESULT：

```bash
python -m freshlatch.eval public-pack --verify
```

通过时打印 `content_hash=<64 位小写 hex> verify=ok`，进程退出码 0。

当前夹具回放的 `content_hash` 为 `06b6032d38fb49f173737d875561f74f696f6763c6ed80f42d4479b7b8dbc50b`。夹具或规范 JSON 变了，这个值会变，`--verify` 仍按重算结果判断。

`--out <目录>` 把同一 RESULT 写成该目录下的 `RESULT.json`。目录不得落在 `docs/evidence/` 或 `data/`。

## 如何核对 content_hash

`content_hash` 是 sha256。输入是 RESULT 去掉 `content_hash` 之后的规范 JSON 字节。

规范 JSON：

- 对象键 `sort_keys=True`
- `separators=(",", ":")`
- `ensure_ascii=False`
- 编码 UTF-8
- 末尾不加换行

同一夹具再跑一次，`content_hash` 相同。`--verify` 按上面的规范字节重算 sha256，再与字段比较。

`pack_sha256` 是夹具文件先把换行折成 LF 之后的 sha256。它写在 RESULT 里，并进入 `content_hash`。Windows 上以 CRLF 检出时，折行后的哈希与 LF 检出相同。

## 独立 abstain

RAGAS alone ≠ ground truth。

`ragas_faithfulness` 只随夹具记录。回放标签不读这个字段。ARES 用少量人工标注校准裁判；裁判分仍然不是 ground truth。本包的 abstain 来自 `system_action=abstain`，再与 `independent_label` 对照。RESULT 里 `abstain_source` 为 `system_action`，`ragas_used_as_label` 为 false，`ragas_is_ground_truth` 为 false。

`pub-abstain-overlap` 的答案包含 context span，引用 id 落在上下文里，`ragas_faithfulness` 为 `1.0`。回放标签是 abstain。`pub-supported-low-ragas` 的 `ragas_faithfulness` 为 `0.0`，引用与 span 都对上，回放标签是 supported。

## CI

CI 路径是 `.github/workflows/ci.yml` 里的 `pytest`。这条路径不需要付费 API。回放不读密钥，不访问网络。冒烟测试：`tests/unit/test_a_p7_public_eval_pack.py`。

## 范围

公开可复现 ≠ 登上权威榜。
