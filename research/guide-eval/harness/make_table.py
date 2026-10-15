import json, os
D = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(D, "results.json")))
Y = lambda b: "Y" if b else "n"; P = lambda b: "**PASS**" if b else "fail"
key = lambda r: ({"sonnet": 0, "opus": 1}[r["model"]], r["arm"] != "without", r["harness"], r["rep"])
for mdl in ("sonnet", "opus"):
    s1 = sorted([r for r in rows if r["story"] == "s1" and r["model"] == mdl], key=key)
    s3 = sorted([r for r in rows if r["story"] == "s3" and r["model"] == mdl], key=key)
    if not s1 and not s3: continue
    name = {"sonnet": "Sonnet 4.6", "opus": "Opus 4.6"}[mdl]
    print(f"### {name}: story 1 (skill-xray; Verify = the real scanner gives T4 / T0)\n")
    print("| arm | harness | rep | tiers (fetch / tone) | scanner fetched | pinned + hash checked | scanner run | PASS | time | tool calls |\n|---|---|---|---|---|---|---|---|---|---|")
    for r in s1:
        g = r["grade"]; b = r["behaviour"]
        t = f'{g["fetch_helper_tier"]} / {g["tone_guide_tier"]}' if g.get("fetch_helper_tier") or g.get("tone_guide_tier") else "own scale"
        ph = ("pinned" if g.get("pinned_commit_used") else ("main" if g.get("unpinned_main_used") else "-")) + (" + hash" if g.get("hash_checked") else "") if g.get("scanner_fetched") else "-"
        print(f'| {r["arm"]} | {r["harness"]} | {r["rep"]} | {t} | {Y(g.get("scanner_fetched"))} | {ph} | {Y(g.get("scanner_run"))} | {P(g.get("PASS"))} | {r["wall_s"]}s | {b.get("tool_calls")} |')
    print(f"\n### {name}: story 3 (author-local dates)\n")
    print("| arm | harness | rep | a own date | b order | c third-zone reader | d no-date caller | PASS new Verify | PASS old Verify | time | tool calls |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for r in s3:
        g = r["grade"]; b = r["behaviour"]; go = r.get("grade_old_verify") or {}
        dd = Y(g.get("d_existing_caller_no_date_ok")) if g.get("d_existing_caller_no_date_ok") else "n: " + str(g.get("legacy_ba_author_sees"))[:40]
        print(f'| {r["arm"]} | {r["harness"]} | {r["rep"]} | {Y(g.get("a_each_author_sees_own_local_date"))} | {Y(g.get("b_feed_order_matches_submission"))} | {Y(g.get("c_third_zone_reader_sees_same_dates"))} | {dd} | {P(g.get("PASS"))} | {P(go.get("PASS"))} | {r["wall_s"]}s | {b.get("tool_calls")} |')
    print()
