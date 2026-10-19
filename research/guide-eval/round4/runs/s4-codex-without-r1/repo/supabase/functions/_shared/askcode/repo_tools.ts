// Read-only tools over one GitHub repo for the ask-code agent (agent.ts),
// through the Hearback.dev installation (Contents: read). Everything is read
// at one commit (the default branch's head when the question was asked), so
// the cited lines match the links.
//
//   search_code    GitHub code search in the repo (default branch index; a
//                  repo GitHub hasn't indexed returns nothing → grep)
//   grep           a regex over the repo's text files, read one by one
//                  (capped), for when search misses
//   list_files     paths under a folder (from the tree, one request)
//   read_file      a file's lines, numbered
//   recent_commits the last commits, optionally for one path

/** GET a GitHub REST path as the installation (GithubApp.asInstallation). */
export type RepoGet = <T>(path: string) => Promise<T>;

export interface ToolDef { name: string; description: string; input_schema: Record<string, unknown> }

export const REPO_TOOLS: ToolDef[] = [
  {
    name: "search_code",
    description: "Search the repository's code (GitHub code search, default branch). Returns matching file paths. Use plain identifiers or words; qualifiers like path:, extension:, language: work.",
    input_schema: { type: "object", properties: { query: { type: "string" } }, required: ["query"] },
  },
  {
    name: "grep",
    description: "Regex search over text files (case-insensitive), optionally under a folder. Slower than search_code: use it when search_code finds nothing or you need the matching lines.",
    input_schema: {
      type: "object",
      properties: { pattern: { type: "string" }, path_prefix: { type: "string", description: "e.g. app/lib/ (optional)" } },
      required: ["pattern"],
    },
  },
  {
    name: "list_files",
    description: "List file paths under a folder (empty for the repository root). At most 300 paths.",
    input_schema: { type: "object", properties: { path_prefix: { type: "string" } } },
  },
  {
    name: "read_file",
    description: "Read a file's lines with line numbers. At most 400 lines per call; pass start_line/end_line for long files.",
    input_schema: {
      type: "object",
      properties: { path: { type: "string" }, start_line: { type: "integer" }, end_line: { type: "integer" } },
      required: ["path"],
    },
  },
  {
    name: "recent_commits",
    description: "The 15 most recent commits (date and message), optionally only those touching a path.",
    input_schema: { type: "object", properties: { path: { type: "string" } } },
  },
];

const TEXT_EXT = /\.(md|markdown|txt|ts|tsx|js|jsx|mjs|cjs|json|ya?ml|toml|dart|py|rb|go|rs|java|kt|swift|c|h|cc|cpp|hpp|cs|php|sql|sh|bash|zsh|html|css|scss|vue|svelte|ex|exs|lua|gradle|xml|env\.example|ini|cfg)$/i;
const SKIP_DIR = /(^|\/)(node_modules|vendor|dist|build|\.dart_tool|\.git|Pods|\.next|coverage)\//;
const MAX_FILE_BYTES = 120_000;
const MAX_READ_LINES = 400;
const GREP_FILES = 40;

interface TreeEntry { path: string; type: string; size?: number }

/** Pure: lines [start, end] of [text], numbered, capped. */
export function numberedLines(text: string, start = 1, end?: number): { text: string; total: number; shown: [number, number] } {
  const lines = text.split("\n");
  const s = Math.max(1, Math.floor(start));
  const e = Math.min(lines.length, Math.floor(end ?? s + MAX_READ_LINES - 1), s + MAX_READ_LINES - 1);
  const out = lines.slice(s - 1, e).map((l, i) => `${s + i}\t${l}`).join("\n");
  return { text: out, total: lines.length, shown: [s, e] };
}

/** Pure: the matching lines of [text] for [re], numbered, at most [max]. */
export function grepLines(text: string, re: RegExp, max = 8): string[] {
  const out: string[] = [];
  for (const [i, l] of text.split("\n").entries()) {
    if (re.test(l)) out.push(`${i + 1}: ${l.trim().slice(0, 200)}`);
    if (out.length >= max) break;
  }
  return out;
}

/** Pure: a file's base64 contents (GitHub wraps lines) → text. */
export function decodeContent(b64: string): string {
  const bin = atob(b64.replace(/\s/g, ""));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

export const blobUrl = (repo: string, sha: string, path: string, start?: number | null, end?: number | null) =>
  `https://github.com/${repo}/blob/${sha}/${path.split("/").map(encodeURIComponent).join("/")}` +
  (start ? `#L${start}${end && end !== start ? `-L${end}` : ""}` : "");

export class RepoTools {
  #tree: TreeEntry[] | null = null;
  #files = new Map<string, string>();
  /** GitHub requests made (the run's report). */
  requests = 0;

  constructor(readonly repo: string, readonly sha: string, private get: RepoGet) {}

  async #req<T>(path: string): Promise<T> {
    this.requests++;
    return await this.get<T>(path);
  }

  async tree(): Promise<TreeEntry[]> {
    if (this.#tree) return this.#tree;
    const r = await this.#req<{ tree: TreeEntry[]; truncated?: boolean }>(`/repos/${this.repo}/git/trees/${this.sha}?recursive=1`);
    return this.#tree = r.tree.filter((e) => e.type === "blob" && !SKIP_DIR.test(e.path));
  }

  async file(path: string): Promise<string> {
    const hit = this.#files.get(path);
    if (hit !== undefined) return hit;
    const r = await this.#req<{ content?: string; encoding?: string; size?: number; type?: string }>(
      `/repos/${this.repo}/contents/${path.split("/").map(encodeURIComponent).join("/")}?ref=${this.sha}`,
    );
    if (r.type !== "file" || r.encoding !== "base64" || r.content === undefined) throw new Error(`${path} is not a readable file`);
    if ((r.size ?? 0) > MAX_FILE_BYTES * 4) throw new Error(`${path} is too large to read (${r.size} bytes)`);
    const text = decodeContent(r.content);
    this.#files.set(path, text);
    return text;
  }

  /** Runs one tool call; errors come back as text for the model, not thrown. */
  async run(name: string, input: Record<string, unknown>): Promise<string> {
    try {
      switch (name) {
        case "search_code": return await this.searchCode(String(input.query ?? ""));
        case "grep": return await this.grep(String(input.pattern ?? ""), typeof input.path_prefix === "string" ? input.path_prefix : "");
        case "list_files": return await this.listFiles(typeof input.path_prefix === "string" ? input.path_prefix : "");
        case "read_file": return await this.readFile(String(input.path ?? ""), Number(input.start_line) || 1, Number(input.end_line) || undefined);
        case "recent_commits": return await this.recentCommits(typeof input.path === "string" ? input.path : "");
        default: return `Unknown tool ${name}.`;
      }
    } catch (e) {
      return `Error: ${(e as Error).message.slice(0, 300)}`;
    }
  }

  async searchCode(query: string): Promise<string> {
    if (!query.trim()) return "Give a query.";
    const q = encodeURIComponent(`${query} repo:${this.repo}`);
    const r = await this.#req<{ total_count: number; items: { path: string }[] }>(`/search/code?q=${q}&per_page=15`);
    if (!r.items.length) return "No results. GitHub may not have indexed this repository: try grep.";
    return `${r.total_count} result(s):\n${r.items.map((i) => i.path).join("\n")}`;
  }

  async grep(pattern: string, prefix: string): Promise<string> {
    let re: RegExp;
    try { re = new RegExp(pattern, "i"); } catch { return `Not a valid regex: ${pattern}`; }
    const files = (await this.tree()).filter((e) => e.path.startsWith(prefix) && TEXT_EXT.test(e.path) && (e.size ?? 0) <= MAX_FILE_BYTES);
    // Paths that mention the pattern first, then the rest in tree order.
    const ranked = [...files.filter((f) => re.test(f.path)), ...files.filter((f) => !re.test(f.path))];
    const out: string[] = [];
    let read = 0;
    for (const f of ranked) {
      if (read >= GREP_FILES) break;
      read++;
      const hits = grepLines(await this.file(f.path), re);
      if (hits.length) out.push(`${f.path}\n  ${hits.join("\n  ")}`);
    }
    const note = ranked.length > read ? `\n(read ${read} of ${ranked.length} files; narrow path_prefix to search the rest)` : "";
    return (out.length ? out.join("\n") : "No matches.") + note;
  }

  async listFiles(prefix: string): Promise<string> {
    const paths = (await this.tree()).filter((e) => e.path.startsWith(prefix)).map((e) => e.path);
    if (!paths.length) return `No files under '${prefix}'.`;
    return paths.slice(0, 300).join("\n") + (paths.length > 300 ? `\n(${paths.length - 300} more)` : "");
  }

  async readFile(path: string, start: number, end?: number): Promise<string> {
    if (!path) return "Give a path.";
    const n = numberedLines(await this.file(path.replace(/^\/+/, "")), start, end);
    return `${path} (lines ${n.shown[0]}–${n.shown[1]} of ${n.total})\n${n.text}`;
  }

  async recentCommits(path: string): Promise<string> {
    const p = path ? `&path=${encodeURIComponent(path)}` : "";
    const r = await this.#req<{ sha: string; commit: { message: string; author?: { date?: string } } }[]>(
      `/repos/${this.repo}/commits?sha=${this.sha}&per_page=15${p}`,
    );
    if (!r.length) return "No commits.";
    return r.map((c) => `${c.sha.slice(0, 7)} ${c.commit.author?.date?.slice(0, 10) ?? ""} ${c.commit.message.split("\n")[0].slice(0, 120)}`).join("\n");
  }
}
