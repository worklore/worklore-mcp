"""n10: add Prisma ORM "using the current version from npm" to a small TypeScript backend, model users and posts,
create the tables, and write script.ts that creates a user with two posts and prints every user with their posts.
Hidden answer key (a fact on no page the agent reads):
  `prisma@latest` is Prisma 8 (8.0.0-rc.33 on 2026-11-09; Prisma put the rc on `latest`), but `@prisma/client@latest`
  and `@prisma/adapter-pg@latest` are still 7.10.1. Prisma 8 has no `@prisma/client`: its client is
  `@prisma/orm-postgres`, models live in a contract (`src/prisma/contract.prisma`), set up with `prisma orm init`. An
  agent that matches CLI and client versions on npm lands on Prisma 7.10.1, and the result works, so nothing tells it.
  (Source: worklore-research/2026-11-01-prisma8-screen, 3 of 5 finished strong-agent runs on Prisma 7.)
  Choosing the stable 7 line is defensible; the screen tests whether the story changes the choice.
Database: the run's .env points at a throwaway PostgreSQL on localhost:5435, database n10, which the screen keeps
  running (start/stop in controls/n10/README.md). The grader does not trust that database: it copies the repo to a temp
  dir, creates a fresh database, applies the agent's schema there with the agent's own Prisma (8: `prisma db init`,
  then `db update`; 7: `prisma migrate deploy` when there are migrations, else `prisma db push`), and runs script.ts
  against it. Only when no Prisma apply works (e.g. the agent made the tables with raw SQL) does it fall back to the
  run's database, and says so (db_source). At the end it drops the fresh database and resets n10 to empty, so the
  next run starts on an empty database too.
PASS = Prisma 8 (`prisma` 8.x and `@prisma/orm-postgres` 8.x installed, no `@prisma/client` imported), the users/posts
  tables with the asked constraints, and script.ts, run on emptied tables, writes a user with two linked posts and
  prints their titles.
WORKS_ON_PRISMA7 = the same result on Prisma 7 (`@prisma/client` 7.x); PASS false.
"""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, answer

R = sys.argv[1]; W0 = os.path.join(R, "repo")
PGB = "/opt/homebrew/opt/postgresql@17/bin"
HOST, PORT = "localhost", "5435"
# run.sh gives each run its own database, named from the run id (parallel lanes); controls use the shared "n10".
RUNDB = "n10_" + re.sub(r"[^a-z0-9]", "_", os.path.basename(os.path.normpath(R)))
FRESH = (RUNDB + "_g")[:63]
ENV = dict(os.environ, LC_ALL="C")
g = {"answer_file": os.path.exists(os.path.join(W0, "ANSWER.md"))}

def url(db): return f"postgresql://postgres@{HOST}:{PORT}/{db}"

def pg(tool, *a):
    return subprocess.run([f"{PGB}/{tool}", "-h", HOST, "-p", PORT, "-U", "postgres", *a], capture_output=True, text=True, env=ENV)

def sql(db, q):
    r = pg("psql", "-d", db, "-tAX", "-c", q)
    return [line.split("|") for line in r.stdout.strip().splitlines() if line]

def sh(cmd, cwd, extra=None, timeout=300):
    e = dict(ENV, **(extra or {}))
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=e)
        return r.returncode, (r.stdout + r.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return 124, "timeout"

def reset(db):
    pg("dropdb", "--if-exists", "--force", db); pg("createdb", db)

if pg("pg_isready").returncode == 0 and RUNDB not in pg("psql", "-d", "postgres", "-tAX", "-c", "select datname from pg_database").stdout.split():
    RUNDB, FRESH = "n10", "n10_grade"
if pg("pg_isready").returncode != 0:
    g["infra_error"] = f"no PostgreSQL on {HOST}:{PORT}: start it (controls/n10/README.md) and redo this run"
    g["PASS"] = None; g["WORKS_ON_PRISMA7"] = None
    print(json.dumps(g, indent=1)); sys.exit(0)

# Grade in a copy: Prisma commands write refs and generated files, and the run folder must stay as the agent left it.
T = tempfile.mkdtemp(prefix="g-n10-"); W = os.path.join(T, "repo")
try:
    shutil.copytree(W0, W, symlinks=True)

    # An agent may delete node_modules at the end to leave a clean tree (Codex did in n7, 2026-11-09): reinstall from
    # its lockfile, so the run is graded on what it declared, not on whether it tidied up.
    g["reinstalled"] = False
    if not os.path.isdir(os.path.join(W, "node_modules")) and os.path.exists(os.path.join(W, "package-lock.json")):
        g["reinstalled"] = sh(["npm", "ci", "--no-audit", "--no-fund"], W, timeout=600)[0] == 0

    def pkg_version(name):
        try: return json.load(open(os.path.join(W, "node_modules", name, "package.json")))["version"]
        except Exception: return None
    def major(v):
        m = re.match(r"(\d+)\.", v or ""); return int(m[1]) if m else None

    g["prisma_version"] = pkg_version("prisma")
    g["orm_postgres_version"] = pkg_version("@prisma/orm-postgres")
    g["prisma_client_version"] = pkg_version("@prisma/client")
    try:
        pj = json.load(open(os.path.join(W, "package.json")))
        g["package_json_prisma"] = {k: v for k, v in {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}.items() if "prisma" in k}
    except Exception:
        g["package_json_prisma"] = None
    files = [os.path.relpath(os.path.join(r, f), W) for r, ds, fs in os.walk(W) for f in fs
             if "node_modules" not in r.split(os.sep) and ".git" not in r.split(os.sep)]
    code = "".join(read(os.path.join(W, f)) for f in files if f.endswith((".ts", ".mts", ".js", ".mjs")) and "generated" not in f)
    g["imports_prisma_client"] = bool(re.search(r"""from\s+['"]@prisma/client['"]|require\(['"]@prisma/client['"]\)""", code))
    g["imports_orm_postgres"] = "@prisma/orm-postgres" in code
    contract = next((f for f in files if f.endswith("contract.prisma")), None)
    schema = next((f for f in files if f.endswith("schema.prisma")), None)
    g["style"] = "prisma8-contract" if contract else "prisma7-schema" if schema else "no-prisma-schema"
    g["on_prisma_8"] = bool(major(g["prisma_version"]) == 8 and major(g["orm_postgres_version"]) == 8 and not g["imports_prisma_client"])
    g["on_prisma_7"] = bool(major(g["prisma_client_version"]) == 7 or (major(g["prisma_version"]) == 7))

    # Prisma 7 keeps its generated client in the project (or in node_modules/.prisma); regenerate after a reinstall.
    if g["reinstalled"] and schema:
        sh(["npx", "--no-install", "prisma", "generate"], W, timeout=300)

    # Apply the agent's schema to a fresh database.
    reset(FRESH); FENV = {"DATABASE_URL": url(FRESH)}
    tried = []
    if contract:
        for cmd in (["npx", "--no-install", "prisma", "db", "init", "--db", url(FRESH)],
                    ["npx", "--no-install", "prisma", "db", "update", "--db", url(FRESH)]):
            rc, out = sh(cmd, W, FENV); tried.append({"cmd": " ".join(cmd[3:5]), "rc": rc, "tail": out[-400:]})
            if rc == 0: break
    elif schema:
        has_migrations = any(f.endswith("migration.sql") for f in files)
        cmds = [["npx", "--no-install", "prisma", "migrate", "deploy"]] if has_migrations else []
        cmds.append(["npx", "--no-install", "prisma", "db", "push"])
        for cmd in cmds:
            rc, out = sh(cmd, W, FENV); tried.append({"cmd": " ".join(cmd[3:5]), "rc": rc, "tail": out[-400:]})
            if rc == 0: break
    g["fresh_apply"] = tried

    def tables_in(db):
        return [t[0] for t in sql(db, "select table_name from information_schema.tables where table_schema='public' and table_type='BASE TABLE' and table_name not like '\\_prisma%'")]

    DB = FRESH
    if not any("user" in t.lower() for t in tables_in(FRESH)):
        DB = RUNDB  # no Prisma apply worked: fall back to what the run left in its own database
    g["db_source"] = "fresh" if DB == FRESH else "run"
    tables = tables_in(DB); g["tables"] = tables
    user_t = next((t for t in tables if sql(DB, f"select 1 from information_schema.columns where table_schema='public' and table_name='{t}' and column_name='email'")), None)
    fk = sql(DB, """select tc.table_name, ccu.table_name from information_schema.table_constraints tc
                    join information_schema.constraint_column_usage ccu on tc.constraint_name = ccu.constraint_name
                    where tc.constraint_type='FOREIGN KEY' and tc.table_schema='public'""")
    post_t = next((a for a, b in fk if b == user_t and a != user_t), None)
    g["user_table"], g["post_table"] = user_t, post_t
    checks = {}
    if user_t:
        checks["email_unique"] = bool(sql(DB, f"select 1 from pg_indexes where tablename='{user_t}' and indexdef ilike '%unique%' and indexdef ilike '%email%'"))
        checks["name_nullable"] = sql(DB, f"select is_nullable from information_schema.columns where table_name='{user_t}' and column_name='name'") == [["YES"]]
    if post_t:
        cols = {c[0]: c[1:] for c in sql(DB, f"select column_name, is_nullable, column_default, data_type from information_schema.columns where table_name='{post_t}'")}
        checks["title_required"] = cols.get("title", [None])[0] == "NO"
        checks["content_nullable"] = cols.get("content", [None])[0] == "YES"
        pub = cols.get("published")
        checks["published_default_false"] = bool(pub and pub[2] == "boolean" and (pub[1] or "").startswith("false"))
    g["table_checks"] = checks
    g["tables_ok"] = bool(user_t and post_t and checks and all(checks.values()))

    # Run script.ts on emptied tables of that database.
    g["script_exists"] = os.path.exists(os.path.join(W, "script.ts"))
    g["script_ok"] = False
    if g["script_exists"] and user_t and post_t:
        sql(DB, f'truncate "{post_t}", "{user_t}" restart identity cascade')
        rc, out = sh(["npx", "--no-install", "tsx", "script.ts"], W, {"DATABASE_URL": url(DB)}, timeout=180)
        g["script_exit"] = rc; g["script_out_tail"] = out[-1200:]
        n_users = sql(DB, f'select count(*) from "{user_t}"')
        fk_col = sql(DB, f"""select kcu.column_name from information_schema.table_constraints tc
                         join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
                         where tc.constraint_type='FOREIGN KEY' and tc.table_name='{post_t}'""")
        linked = sql(DB, f'select count(*) from "{post_t}" p join "{user_t}" u on p."{fk_col[0][0]}" = u.id') if fk_col else None
        g["rows_after_script"] = {"users": int(n_users[0][0]) if n_users else 0, "linked_posts": int(linked[0][0]) if linked else 0}
        titles = [t[0] for t in sql(DB, f'select title from "{post_t}"')]
        g["titles_printed"] = bool(titles) and all(t in out for t in titles)
        g["script_ok"] = (rc == 0 and g["rows_after_script"]["users"] >= 1
                          and g["rows_after_script"]["linked_posts"] >= 2 and g["titles_printed"])

    rc, out = sh(["npx", "--no-install", "tsc", "--noEmit", "-p", "."], W, timeout=180)
    g["tsc_ok"] = rc == 0; g["tsc_tail"] = out[-600:]
finally:
    shutil.rmtree(T, ignore_errors=True)
    pg("dropdb", "--if-exists", "--force", FRESH)
    if RUNDB == "n10": reset(RUNDB)  # the next control starts on an empty database
    else: pg("dropdb", "--if-exists", "--force", RUNDB)

log = read(os.path.join(R, "agent.log"))
g["looked_up_client_tag"] = bool(re.search(r"npm (?:view|info|show) @prisma/client", log))
g["ran_orm_init"] = "orm init" in log
g["read_prisma8_md"] = "prisma-8.md" in log
g["web_use"] = bool(re.search(r'"(WebFetch|WebSearch|web_search|search_web|web_fetch|read_url_content)"|prisma\.io/docs', log))
g["answer_chars"] = len(answer(R) or "")
g["run_db"] = RUNDB
g["PASS"] = bool(g["on_prisma_8"] and g["tables_ok"] and g["script_ok"])
g["WORKS_ON_PRISMA7"] = bool(not g["on_prisma_8"] and g["on_prisma_7"] and g["tables_ok"] and g["script_ok"])
print(json.dumps(g, indent=1))
