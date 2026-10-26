# -*- coding: utf-8 -*-
"""plan_gate.py — 規劃層機械閘門（viral-playbook 站1-2 的可執行版）

script_gate 管腳本，本檔管「腳本之前」：選題與包裝先行有沒有照爆款手冊做。
輸入 = 規劃文件純文字（格式見 examples/PLAN_TEMPLATE.md）。

fail 級（缺了=還沒想清楚，不准往下寫稿）：
  P1 框架標籤    框架：成就/蛻變 或 工具/教學（成就/蛻變框架通常強於工具框架，見 knowledge/viral-playbook-framework.md）
  P2 機器歸屬    機器：推薦 或 搜尋（雙機器分流，viral-playbook 站1）
  P3 包裝先行    「## 包裝候選」段 ≥8 組「標題 | 縮圖」配對（kill 門檻）
  P4 合規        行首「合規：通過 YYYY-MM-DD 複核：姓名」人工簽章（真實非未來日期＋真人複核人；否定/待辦/佔位字、機器複核人不算；維護者 2026-10-25 決定採用上游 Package D）
  P5 cluster    cluster關鍵字：XXX（語義方向盤）
warn 級：
  W1 無 Expected Views 對標行（快篩基準）
  W2 工具框架 + 機器：推薦 組合（documented 反指標，見 knowledge/viral-playbook-framework.md）

API: gate_plan(text) -> (ok, report)
CLI: python plan_gate.py <plan.md> / python plan_gate.py （self-test）
cp950 安全：console ASCII+中文無 emoji；I/O utf-8。
"""
from __future__ import annotations

import io
import os
import re
import sys
from datetime import date, timedelta

try:
    from gate_core import is_placeholder
except ImportError:                                  # 從別的 cwd 或單檔複製時
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gate_core import is_placeholder

_FRAME_RE = re.compile(r"框架[:：]\s*(成就|蛻變|工具|教學|身分)")
_MACHINE_RE = re.compile(r"機器[:：]\s*(推薦|搜尋)")
_PKG_HEAD_RE = re.compile(r"^#+\s*包裝候選", re.MULTILINE)
_PAIR_RE = re.compile(r"^\s*(?:\d+[.)、]|[-*])\s*.+?\s*\|\s*.+$", re.MULTILINE)
# P4 只認行首的合規章（可帶 - / 1. / > 前綴）；句中提到「合規：通過」不算數
_COMPLIANCE_LINE_RE = re.compile(
    r"^[ \t>]*(?:[-*+][ \t]+|\d+[.)、][ \t]*)?合規[:：][ \t]*(.*)$", re.MULTILINE)
_STATUS_RE = re.compile(r"(?:通過|PASS|✓)")
_STAMP_NEGATION_RE = re.compile(
    r"待|尚未|還沒|之前|以前|撤回|否|未(?:通過|完成|複核|審|確認|跑)"
    r"|不(?:准|得|可|能|通過|合規|行)|沒(?:有|通過|過|跑)"
    r"|(?<![A-Za-z])(?:not|pending|todo|tbd)(?![A-Za-z])", re.IGNORECASE)
_ISO_DATE_RE = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")
_REVIEWER_RE = re.compile(
    r"(?:複核人?|審核人?|reviewer|reviewed by)[ \t]*[:：][ \t]*([^\s,，;；、/／()（）|｜]+)",
    re.IGNORECASE)
_MACHINE_REVIEWERS = {"ai", "bot", "auto", "agent", "machine", "codex", "claude", "gpt",
                      "chatgpt", "程式", "機器", "自動", "系統"}
_CLUSTER_RE = re.compile(r"cluster\s*關鍵字[:：]\s*\S+", re.IGNORECASE)
_EXPECTED_RE = re.compile(r"Expected\s*Views|期望值對標", re.IGNORECASE)
# 模板佔位字：沒換掉就等於沒填（PLAN_TEMPLATE.md 原樣不得過關）
_PLACEHOLDER_RE = re.compile(
    r"(?<![A-Za-z])(?:TODO|TBD|FIXME|YYYY|MM-DD)(?![A-Za-z])|你的主題詞", re.IGNORECASE)
# 包裝候選只認「整格」佔位（標題候選一 / 縮圖概念一 / TODO），真標題裡出現「概念一次」不算
_PAIR_CELL_PLACEHOLDER_RE = re.compile(
    r"(?:標題|縮圖)?(?:候選|概念)[一二三四五六七八九十0-9０-９]+|TODO|TBD|待補|\.{3}|…",
    re.IGNORECASE)


def _is_placeholder_pair(line: str) -> bool:
    body = re.sub(r"^\s*(?:\d+[.)、]|[-*])\s*", "", line)
    return any(_PAIR_CELL_PLACEHOLDER_RE.fullmatch(cell.strip()) for cell in body.split("|"))


def _line_at(text: str, match) -> str:
    start = text.rfind("\n", 0, match.start()) + 1
    end = text.find("\n", match.end())
    return text[start:] if end < 0 else text[start:end]


def _stamp_problem(rest: str):
    """單一合規章 → 問題描述；None = 有效（通過 + 真實 ISO 日期 + 真人複核人，無否定/佔位字）。"""
    rest = re.sub(r"\s+", " ", rest).strip()
    status = _STATUS_RE.match(rest)
    if not status:
        return "合規狀態不是『通過』（%s）" % rest[:24]
    tail = rest[status.end():]
    if _STAMP_NEGATION_RE.search(tail) or (tail.strip() and is_placeholder(tail)):
        return "合規章含否定、待辦或佔位字（%s）" % rest[:40]
    day = _ISO_DATE_RE.search(tail)
    if not day:
        return "合規章缺 ISO 日期"
    try:
        stamped = date(*(int(part) for part in day.groups()))
    except ValueError:
        return "合規章日期不存在（%s）" % day.group(0)
    if stamped > date.today() + timedelta(days=1):
        return "合規章日期在未來（%s）" % day.group(0)
    who = _REVIEWER_RE.search(tail)
    if not who or is_placeholder(who.group(1)) \
            or who.group(1).casefold() in _MACHINE_REVIEWERS:
        return "合規章缺真人複核人"
    return None


def _compliance_problem(text: str):
    """P4：每一個行首合規章都要有效（矛盾的多個章 = 不過）；None = 過。"""
    stamps = _COMPLIANCE_LINE_RE.findall(text)
    if not stamps:
        return "缺合規標記"
    for rest in stamps:
        problem = _stamp_problem(rest)
        if problem:
            return problem
    return None


def gate_plan(text: str):
    if not isinstance(text, str):
        return False, {"ok": False, "warns": [], "pairs": 0,
                       "fails": ["P0 規劃文件必須是文字，收到 %s（拒收，不當成空文件猜）"
                                 % type(text).__name__]}
    fails, warns = [], []

    m_frame = _FRAME_RE.search(text)
    if not m_frame:
        fails.append("P1 缺框架標籤（框架：成就/工具...）")
    m_machine = _MACHINE_RE.search(text)
    if not m_machine:
        fails.append("P2 缺機器歸屬（機器：推薦/搜尋）")

    pkg = _PKG_HEAD_RE.search(text)
    n_pairs = n_template = 0
    if pkg:
        seg = text[pkg.end():]
        nxt = re.search(r"^#+\s", seg, re.MULTILINE)
        seg = seg[: nxt.start()] if nxt else seg
        pairs = _PAIR_RE.findall(seg)
        n_pairs = len([p for p in pairs if not _is_placeholder_pair(p)])
        n_template = len(pairs) - n_pairs
    if n_pairs < 8:
        fails.append("P3 包裝候選不足（%d/8 組『標題 | 縮圖』；包不出來=砍題）" % n_pairs
                     + ("；另有 %d 組仍是模板佔位，不算數" % n_template if n_template else ""))

    problem = _compliance_problem(text)
    if problem:
        fails.append("P4 %s（行首寫：合規：通過 YYYY-MM-DD 複核：姓名 = 平台 AI 內容政策 checklist 人工先過）"
                     % problem)
    m_cluster = _CLUSTER_RE.search(text)
    if not m_cluster:
        fails.append("P5 缺 cluster 關鍵字")
    elif _PLACEHOLDER_RE.search(_line_at(text, m_cluster)):
        fails.append("P5 cluster 關鍵字仍是模板佔位")

    if not _EXPECTED_RE.search(text):
        warns.append("W1 無 Expected Views 對標行")
    if m_frame and m_machine and m_frame.group(1) in ("工具", "教學", "身分") \
            and m_machine.group(1) == "推薦":
        warns.append("W2 工具框架 x 推薦機 = documented 輸家組合（見 knowledge/viral-playbook-framework.md），改成就框架或改搜尋機定位")

    ok = not fails
    return ok, {"ok": ok, "fails": fails, "warns": warns, "pairs": n_pairs}


def _stamp(day=None, who="編輯甲") -> str:
    """self-test 用的合規章；日期在執行時算（原始碼不寫死日期）。"""
    return "合規：通過 %s 複核：%s（政策 checklist）" % (
        (day or date.today()).isoformat(), who)


def _fails_on(text: str, *rules) -> bool:
    ok, rep = gate_plan(text)
    return (not ok) and all(any(f.startswith(rule) for f in rep["fails"]) for rule in rules)


def _selftest() -> int:
    fails = []

    def check(name, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", name))
        if not cond:
            fails.append(name)

    good = (
        "# 示範片0X 規劃\n框架：成就\n機器：推薦\ncluster關鍵字：示範主題\n"
        + _stamp() + "\nExpected Views 對標：9,999 中位 x3\n"
        "## 包裝候選\n" + "\n".join(
            "%d. 實際標題%d | 實際縮圖%d" % (i, i, i) for i in range(1, 10)) + "\n## 其他\n"
    )
    ok1, r1 = gate_plan(good)
    check("good plan passes", ok1)
    check("good plan 9 pairs", r1["pairs"] == 9)
    check("good plan no W2", not any(w.startswith("W2") for w in r1["warns"]))

    bad = "# 規劃\n想做一支影片講 AI。\n"
    ok2, r2 = gate_plan(bad)
    check("empty plan fails", not ok2)
    check("all 5 fails flagged", len(r2["fails"]) == 5)

    loser = good.replace("框架：成就", "框架：工具")
    ok3, r3 = gate_plan(loser)
    check("tool-frame x browse warns W2",
          ok3 and any(w.startswith("W2") for w in r3["warns"]))

    few = good.replace("## 包裝候選\n", "## 包裝候選\n").split("## 包裝候選")
    few_text = few[0] + "## 包裝候選\n1. 只有一組 | 縮圖\n## 其他\n"
    ok4, r4 = gate_plan(few_text)
    check("few pairs fails P3", not ok4 and any("P3" in f for f in r4["fails"]))

    tpl = good.replace(_stamp(), "合規：待複核").replace("示範主題", "你的主題詞")
    ok5, r5 = gate_plan(tpl)
    check("template placeholders fail P4/P5",
          not ok5 and {f[:2] for f in r5["fails"]} == {"P4", "P5"})

    today = date.today()
    stamp = _stamp()
    bad_stamps = {
        "negated note line": "說明：合規：通過 之前不准開錄（待人工複核）",
        "line-start negation": "合規：通過 之前不准開錄（待人工複核）",
        "negated despite date": _stamp(who="編輯甲 之前不准開錄"),
        "pending": "合規：待複核",
        "placeholder date": "合規：通過（政策 checklist YYYY-MM-DD）",
        "no date": "合規：通過 複核：編輯甲",
        "no reviewer": "合規：通過 %s（政策 checklist）" % today.isoformat(),
        "placeholder reviewer": _stamp(who="{你的名字}"),
        "machine reviewer": _stamp(who="AI"),
        "future date": _stamp(day=today + timedelta(days=30)),
        "impossible date": "合規：通過 %d-02-30 複核：編輯甲" % today.year,
        "conflicting stamps": stamp + "\n合規：待複核",
    }
    for name, line in bad_stamps.items():
        check("P4 blocks %s" % name, _fails_on(good.replace(stamp, line), "P4"))
    check("bullet-prefixed stamp passes", gate_plan(good.replace(stamp, "- " + stamp))[0])
    check("old unsigned stamp 合規：通過（政策 checklist）now fails P4",
          _fails_on(good.replace(stamp, "合規：通過（政策 checklist）"), "P4"))

    print("-" * 50)
    if fails:
        print("SELFTEST RED: %d failed" % len(fails))
        return 1
    print("SELFTEST GREEN: all checks passed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ok, rep = gate_plan(io.open(sys.argv[1], encoding="utf-8").read())
        print("PLAN GATE:", "PASS" if ok else "FAIL")
        for f in rep["fails"]:
            print("  FAIL -", f)
        for w in rep["warns"]:
            print("  WARN -", w)
        raise SystemExit(0 if ok else 1)
    raise SystemExit(_selftest())
