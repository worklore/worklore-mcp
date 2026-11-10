# n10 PostgreSQL

The n10 task needs a database during the run ("Create the tables in the database"). The fixture's `.env` points at
`postgresql://postgres@localhost:5435/n10`, a throwaway PostgreSQL 17 (trust auth, TCP only, data under the session
scratchpad). The grader resets `n10` to empty after every run, so sequential runs each start on an empty database; it
does its own grading in a fresh database `n10_grade`. Runs must be sequential (screen.sh is).

Start (once; the cluster already exists after the first init):

    SP=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/c317cfd3-ec21-4f89-9953-a8bd39262f92/scratchpad
    PG=/opt/homebrew/opt/postgresql@17/bin
    [ -d $SP/n10-pg ] || $PG/initdb -D $SP/n10-pg -U postgres --auth=trust -E UTF8 --locale=C
    LC_ALL=C $PG/pg_ctl -D $SP/n10-pg -o "-p 5435 -c unix_socket_directories= -c listen_addresses=localhost" -l $SP/n10-pg.log start
    $PG/dropdb -h localhost -p 5435 -U postgres --if-exists --force n10; $PG/createdb -h localhost -p 5435 -U postgres n10

Stop after the screen:

    $PG/pg_ctl -D $SP/n10-pg stop

LC_ALL=C is needed (without it the postmaster refuses to start: "became multithreaded during startup"), and the
socket directory is off because the scratchpad path is longer than the 103-byte socket limit.
If the server is down, the grader prints `infra_error` and PASS null: redo that run.
