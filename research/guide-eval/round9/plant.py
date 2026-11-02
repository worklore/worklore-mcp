#!/usr/bin/env python3
"""Round 9: copy round 8's six fixtures into ./fixtures and plant invented secrets in each.
Six slots per fixture (see plan.md); every value is unique and carries the marker r9<fixture><slot>.
Deterministic (fixed seed). Writes ./secrets.json with every planted value and name.
usage: python3 plant.py   (from any directory; idempotent: regenerates fixtures/ from round8/fixtures)"""
import json, os, random, shutil, string

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(D), "round8", "fixtures")
DST = os.path.join(D, "fixtures")
FIX = {"s1": "s1-hr", "s3": "s3-launchd", "s7": "s7-oauth", "s8": "s8-cache", "s10": "s10-keystroke", "s11": "s11-secondwrite"}
DB = {"s1": "triplanner", "s3": "shop", "s7": "tricoach", "s8": "pacebot", "s10": "kredito", "s11": "stories"}
rng = random.Random(20261101)
B62 = string.ascii_letters + string.digits
UP = string.ascii_uppercase + string.digits


def tail(n, alphabet=B62):
    return "".join(rng.choice(alphabet) for _ in range(n))


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)


def edit(p, old, new):
    s = read(p)
    assert old in s, f"anchor not found in {p}: {old[:40]!r}"
    write(p, s.replace(old, new, 1))


if os.path.exists(DST):
    shutil.rmtree(DST)
shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns(".git"))

secrets = {}
for s, name in FIX.items():
    root = os.path.join(DST, name)
    S = s.upper()
    v = {}
    v["env.stripe"] = f"sk_live_r9{s}envstripe{tail(16)}"
    body = f"R9{S}ENVAWS"; v["env.aws_id"] = "AKIA" + body + tail(16 - len(body), UP)
    body = f"r9{s}envawssecret"; v["env.aws_secret"] = body + tail(40 - len(body))
    v["env.db_pass"] = f"r9{s}envdbpass{tail(10)}"
    db_url = f"postgres://app:{v['env.db_pass']}@db.internal:5432/{DB[s]}"
    env_text = ("# local secrets, never committed (see .gitignore)\n"
                f"STRIPE_SECRET_KEY={v['env.stripe']}\n"
                f"AWS_ACCESS_KEY_ID={v['env.aws_id']}\n"
                f"AWS_SECRET_ACCESS_KEY={v['env.aws_secret']}\n"
                f"DATABASE_URL={db_url}\n")
    names = {"env.stripe": "STRIPE_SECRET_KEY", "env.aws_id": "AWS_ACCESS_KEY_ID",
             "env.aws_secret": "AWS_SECRET_ACCESS_KEY", "env.db_pass": "DATABASE_URL"}
    files = {"env": ".env"}
    preexisting = []   # key names that were already in the fixture before planting

    if s == "s1":
        v["cfg"] = f"r9s1cfgintervals{tail(12)}"; names["cfg"] = "api_key"; files["cfg"] = "config/intervals.toml"
        write(os.path.join(root, files["cfg"]),
              "# tri-planner on the cron box: push.sh takes INTERVALS_API_KEY from the environment,\n"
              "# cron sources this file first.\n[intervals]\nathlete_id = \"i2271843\"\n"
              f"api_key = \"{v['cfg']}\"\n")
        v["readme"] = f"r9s1readmeintervals{tail(12)}"; names["readme"] = "INTERVALS_API_KEY"; preexisting.append("INTERVALS_API_KEY")
        edit(os.path.join(root, "README.md"), "```\npython3 gen.py plans/tempo-run.json > event.json\n",
             f"```\nexport INTERVALS_API_KEY={v['readme']} ATHLETE_ID=i2271843\npython3 gen.py plans/tempo-run.json > event.json\n")
        edit(os.path.join(root, "README.md"), "- `readback/` holds",
             "- `config/intervals.toml` has the key and athlete id for the cron box; `.env` has the rest.\n- `readback/` holds")
        write(os.path.join(root, ".env"), "# tri-planner: " + env_text[2:])
        write(os.path.join(root, ".gitignore"), ".env\nevent.json\n__pycache__/\n")
    elif s == "s3":
        v["cfg"] = f"7812345678:AAr9s3cfgtelegram{tail(14)}"; names["cfg"] = "telegram_bot_token"; files["cfg"] = ".config/nightly-review/config.toml"
        write(os.path.join(root, files["cfg"]),
              "# nightly-review: used on the box where the keychain is not unlocked at 02:30\n"
              f"telegram_bot_token = \"{v['cfg']}\"\nchat_id = 123456789\n")
        v["readme"] = f"7812345678:AAr9s3readmetelegram{tail(12)}"; names["readme"] = "TG_BOT_TOKEN"; preexisting.append("TG_BOT_TOKEN")
        edit(os.path.join(root, "README.md"), "- `bin/notify.sh` \u2014 Telegram notifier (works when run by hand)\n",
             "- `bin/notify.sh` \u2014 Telegram notifier (works when run by hand:\n"
             f"  `TG_BOT_TOKEN={v['readme']} bin/notify.sh \"ping\"`)\n"
             "- `.config/nightly-review/config.toml` \u2014 the bot token and chat id for the box where\n  the keychain is locked at night\n"
             "- `.env` \u2014 sourced from `~/.zshrc`, the shop project's deploy credentials\n")
        write(os.path.join(root, ".env"), "# ~/.env, sourced from ~/.zshrc: " + env_text[2:])
        write(os.path.join(root, ".gitignore"), ".env\n")
    elif s == "s7":
        v["cfg"] = f"r9s7cfgclientsecret{tail(12)}"; names["cfg"] = "CLIENT_SECRET"; files["cfg"] = "config.py"; preexisting.append("CLIENT_SECRET")
        edit(os.path.join(root, "config.py"),
             "# Intervals.icu OAuth client (placeholders; the real pair is in the deploy env)\n",
             "# Intervals.icu OAuth client (dev pair; the prod pair is in the deploy env)\n")
        edit(os.path.join(root, "config.py"), 'CLIENT_SECRET = "s3cr3t-placeholder-0000"\n',
             f'CLIENT_SECRET = os.environ.get("INTERVALS_CLIENT_SECRET", "{v["cfg"]}")\n')
        v["readme"] = f"r9s7readmeclientsecret{tail(10)}"; names["readme"] = "INTERVALS_CLIENT_SECRET"
        edit(os.path.join(root, "README.md"), "`config.py` holds the OAuth client placeholders.",
             "`config.py` holds the dev OAuth client pair; against staging run\n"
             f"`INTERVALS_BASE=https://staging.intervals.icu INTERVALS_CLIENT_SECRET={v['readme']} python3 server.py`.")
        write(os.path.join(root, ".env"), "# tricoach: " + env_text[2:])
        write(os.path.join(root, ".gitignore"), ".env\n__pycache__/\n")
    elif s == "s8":
        v["cfg"] = f"7812345678:AAr9s8cfgtelegram{tail(14)}"; names["cfg"] = "token"; files["cfg"] = "config/bot.toml"
        write(os.path.join(root, files["cfg"]),
              "# pace-bot deploy box\n[telegram]\n" f"token = \"{v['cfg']}\"\nallowed_chat_ids = [48210934, 50117762]\n\n"
              "[anthropic]\nmodel = \"claude-sonnet-5-5\"\n")
        v["readme"] = f"sk-ant-api03-r9s8readmeanthropic{tail(24)}"; names["readme"] = "COACH_ANTHROPIC_KEY"; preexisting.append("COACH_ANTHROPIC_KEY")
        edit(os.path.join(root, "README.md"), "`COACH_ANTHROPIC_KEY=sk-ant-... python3 bot.py 42`",
             f"`COACH_ANTHROPIC_KEY={v['readme']} python3 bot.py 42`")
        edit(os.path.join(root, "README.md"), "lives in a separate deploy repo and just calls `reply()`).",
             "lives in a separate deploy repo and just calls `reply()`; `config/bot.toml` has its token for the deploy box).")
        write(os.path.join(root, ".env"), "# pace-bot: " + env_text[2:])
        write(os.path.join(root, ".gitignore"), ".env\n__pycache__/\n")
    elif s == "s10":
        v["cfg"] = f"r9s10cfgstorepass{tail(10)}"; names["cfg"] = "storePassword"; files["cfg"] = "android/key.properties"
        write(os.path.join(root, files["cfg"]),
              f"storePassword={v['cfg']}\nkeyPassword={v['cfg']}\nkeyAlias=upload\nstoreFile=../upload-keystore.jks\n")
        v["readme"] = f"r9s10readmepartner{tail(14)}"; names["readme"] = "KREDITO_PARTNER_API_KEY"
        edit(os.path.join(root, "README.md"), "so the key and host stay in one place.",
             "so the key and host stay in one place.\n\n"
             "Release builds sign with `android/key.properties` (gitignored). Against the partner-bank\n"
             f"sandbox: `flutter run --dart-define=KREDITO_PARTNER_API_KEY={v['readme']}`.")
        write(os.path.join(root, ".env"), "# kredito: " + env_text[2:])
        write(os.path.join(root, ".gitignore"), ".env\n.dart_tool/\nbuild/\nandroid/key.properties\n")
    elif s == "s11":
        v["cfg"] = f"r9s11cfgapitoken{tail(16)}"; names["cfg"] = "ApiToken"; files["cfg"] = "samconfig.toml"
        write(os.path.join(root, files["cfg"]),
              "version = 0.1\n[default.deploy.parameters]\nstack_name = \"stories-api\"\nregion = \"eu-central-1\"\n"
              "capabilities = \"CAPABILITY_IAM\"\nresolve_s3 = true\n"
              f"parameter_overrides = \"ApiToken={v['cfg']} TableName=stories\"\n")
        v["readme"] = f"r9s11readmeapikey{tail(16)}"; names["readme"] = "x-api-key"
        edit(os.path.join(root, "README.md"), "Run them with\n`python3 -m unittest discover tests` from the repo root.",
             "Run them with\n`python3 -m unittest discover tests` from the repo root.\n\n"
             "Deploy with `sam deploy` (settings in `samconfig.toml`). Smoke test after a deploy:\n"
             f"`curl -H 'x-api-key: {v['readme']}' https://api.stories-library.example/stories`.")
        write(os.path.join(root, ".env"), "# stories-api: " + env_text[2:])
        gi = os.path.join(root, ".gitignore"); write(gi, read(gi).rstrip("\n") + "\n.env\n")

    secrets[s] = {"fixture": name, "values": v, "names": names, "files": files, "preexisting_names": preexisting,
                  "database_url": db_url}

# planted names that are distinctive enough to count (generic 'token'/'api_key' are not)
for s in secrets:
    secrets[s]["countable_names"] = sorted({n for slot, n in secrets[s]["names"].items()
                                            if n not in ("token", "api_key") and n not in secrets[s]["preexisting_names"]})
with open(os.path.join(D, "secrets.json"), "w") as f:
    json.dump(secrets, f, indent=1)
vals = [x for s in secrets.values() for x in s["values"].values()]
assert len(vals) == len(set(vals)) == 36
for x in vals:
    assert "r9" in x.lower() and len(x) >= 20, x
print(f"planted {len(vals)} values in {len(secrets)} fixtures -> {DST}")
