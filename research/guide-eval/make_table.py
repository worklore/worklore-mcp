import json, os
D = os.path.dirname(os.path.abspath(__file__))
rows = {r["id"]: r for r in json.load(open(os.path.join(D, "results.json")))}
A = ["claude", "codex", "agy-pro", "agy-flash"]; Y = lambda b: "Y" if b else "n"
P = lambda g: "**PASS**" if g["PASS"] else "fail"
print("### Story 1: skill-xray (Verify: the real scanner gives T4 and T0)\n")
print("| agent | arm | tiers (fetch / tone) | scanner fetched | scanner run | PASS | time |\n|---|---|---|---|---|---|---|")
for a in A:
    for arm in ["without", "with"]:
        r = rows[f"s1-{a}-{arm}"]; g = r["grade"]
        t = f'{g["fetch_helper_tier"]} / {g["tone_guide_tier"]}' if g["fetch_helper_tier"] else "its own scale"
        print(f'| {a} | {arm} | {t} | {Y(g["scanner_fetched"])} | {Y(g["scanner_run"])} | {P(g)} | {r["wall_s"]}s |')
print("\n### Story 2: MCP client-path tests\n")
print("a = client harness (initialize, then tools/list, then tools/call, checked against the published outputSchema); b = new tests fail when the fix is reverted (tools.py restored); c = new tests pass with the fix; prod = hidden check against the untouched DynamoStore; d = the fake returns production types (Decimal)\n")
print("| agent | arm | a | b | c | prod fixed | d | PASS | time |\n|---|---|---|---|---|---|---|---|---|")
for a in A:
    for arm in ["without", "with"]:
        r = rows[f"s2-{a}-{arm}"]; g = r["grade"]
        av = "Y" if g["a_client_harness"] else ("partial: schema read from source" if g.get("a_client_harness_any_schema") else "n")
        d = g["d_fake_applies_prod_types"] + (" (tests hit DynamoStore directly)" if g["d_fake_applies_prod_types"] == "no" and g["tests_use_production_store"] else "")
        print(f'| {a} | {arm} | {av} | {Y(g["b_catches_bug"])} | {Y(g["c_tests_pass_with_fix"])} | {Y(g["e_production_fixed"])} | {d} | {P(g)} | {r["wall_s"]}s |')
print("\n### Story 3: author-local dates\n")
print("Verify: a = each author sees their own local date (23:30 in UTC+9 and in UTC-3); b = feed order matches submission order. The other columns are extra checks and do not affect PASS.\n")
print("| agent | arm | a | b | 3-zone order | same date for every viewer | old call `publish(entry, client_tz)` still right | PASS | time |\n|---|---|---|---|---|---|---|---|---|")
for a in A:
    for arm in ["without", "with"]:
        r = rows[f"s3-{a}-{arm}"]; g = r["grade"]
        leg = "Y" if g["x_legacy_api_correct"] else "n: " + str(g["legacy_ba_author_sees"])[:48]
        print(f'| {a} | {arm} | {Y(g["a_each_author_sees_own_local_date"])} | {Y(g["b_feed_order_matches_submission"])} | {Y(g["x3_three_zone_order_ok"])} | {Y(g["x_date_viewer_independent"])} | {leg} | {P(g)} | {r["wall_s"]}s |')
