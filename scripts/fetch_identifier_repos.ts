/**
 * Fetches the repos listed in benchmark/identifier_repos.json into eval-repos/id-<name> at PINNED commits.
 *
 *   npx tsx scripts/fetch_identifier_repos.ts [name ...]
 *
 * - First run: shallow-clones the default branch and records the resolved SHA in
 *   benchmark/identifier_repos.lock.json (commit that file: it is the pin).
 * - Later runs / other machines: fetches exactly the SHA in the lock file (git fetch --depth 1 origin <sha>).
 * - Entries with "local" reuse an existing eval-repos/<dir> through a symlink and pin whatever it is at.
 */
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MANIFEST = path.join(ROOT, "benchmark", "identifier_repos.json");
const LOCK = path.join(ROOT, "benchmark", "identifier_repos.lock.json");
const manifest = JSON.parse(readFileSync(MANIFEST, "utf-8")) as {
  repos: { name: string; lang: string; url?: string; local?: string; seen?: boolean }[];
};
const lock: Record<string, { sha: string; url?: string }> = existsSync(LOCK) ? JSON.parse(readFileSync(LOCK, "utf-8")) : {};
const only = process.argv.slice(2);
const git = (cwd: string, ...a: string[]) => execFileSync("git", a, { cwd, encoding: "utf-8", stdio: ["ignore", "pipe", "inherit"] }).trim();

for (const r of manifest.repos) {
  if (only.length && !only.includes(r.name)) continue;
  const dir = path.join(ROOT, "eval-repos", `id-${r.name}`);
  if (r.local) {
    const src = path.join(ROOT, "eval-repos", r.local);
    if (!existsSync(dir)) symlinkSync(src, dir);
    lock[r.name] = { sha: git(src, "rev-parse", "HEAD"), url: git(src, "remote", "get-url", "origin") };
    console.log(`${r.name}: local ${r.local} @ ${lock[r.name].sha.slice(0, 12)}`);
  } else if (existsSync(path.join(dir, ".git"))) {
    const head = git(dir, "rev-parse", "HEAD");
    if (lock[r.name] && lock[r.name].sha !== head) throw new Error(`${r.name}: checkout ${head} != pinned ${lock[r.name].sha}`);
    lock[r.name] = { sha: head, url: r.url };
    console.log(`${r.name}: present @ ${head.slice(0, 12)}`);
  } else if (lock[r.name]) {
    mkdirSync(dir, { recursive: true });
    git(dir, "init", "-q");
    git(dir, "remote", "add", "origin", r.url!);
    git(dir, "fetch", "-q", "--depth", "1", "origin", lock[r.name].sha);
    git(dir, "checkout", "-q", "FETCH_HEAD");
    console.log(`${r.name}: fetched pinned ${lock[r.name].sha.slice(0, 12)}`);
  } else {
    git(ROOT, "clone", "-q", "--depth", "1", r.url!, dir);
    lock[r.name] = { sha: git(dir, "rev-parse", "HEAD"), url: r.url };
    console.log(`${r.name}: cloned, pinned ${lock[r.name].sha.slice(0, 12)}`);
  }
  writeFileSync(LOCK, JSON.stringify(lock, null, 1) + "\n");
}
