/**
 * Docstring-style natural-language query extraction for any repository, using the SAME tree-sitter grammars and
 * definition node types as the identifier suite (scripts/extract_roles.ts), so labels stay consistent.
 *
 *   npx tsx scripts/extract_docqueries.ts <repoDir> <lang> <candidates.json> [--strip <dstDir>]
 *
 * For every function/method/type definition it finds the doc comment directly above it (language specific:
 * triple-slash lines for Rust and C#, javadoc-style blocks for Scala and TypeScript, block or double-slash runs
 * for C/C++, `-- |` for Haskell, `@doc` for Elixir) and turns the first sentence into a query. Candidates are
 * written with their file and name.
 *
 * With --strip, the repo is cloned (copy-on-write on APFS) to <dstDir> and EVERY doc comment attached to a
 * definition is removed from that copy, in all files of the language. That mirrors CodeSearchNet, where the
 * docstring is the query and is not part of the indexed code, and it keeps documented and undocumented code
 * on equal footing. Non-doc comments are untouched. Sampling and scoring are done elsewhere
 * (miru_kalpana/gen_queries_doc.py), so this script has no seed and makes no selection beyond the filters below.
 */
import { execFileSync } from "node:child_process";
import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { CLASS_TYPES, defName, EX_FUNC, FUNC_TYPES, HS_TYPE_DECLS, parserFor } from "./extract_roles.ts";
import type { Node } from "web-tree-sitter";

// Miru chunks .c as C and every other C-family extension (including .h) as C++, so do the same here.
const LANG_EXTS: Record<string, Record<string, string>> = {
  c: { ".c": "c", ".h": "cpp" },
  cpp: { ".h": "cpp", ".hpp": "cpp", ".hh": "cpp", ".hxx": "cpp", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp" },
  csharp: { ".cs": "csharp" },
  scala: { ".scala": "scala" },
  haskell: { ".hs": "haskell" },
  elixir: { ".ex": "elixir", ".exs": "elixir" },
  rust: { ".rs": "rust" },
  typescript: { ".ts": "typescript", ".tsx": "typescript", ".mts": "typescript" },
};
// Same exclusions as miru_kalpana/gen_queries_multi.py, plus vendored/generated directories the identifier suite
// did not need to name (redis deps/, etc.). Applies to query selection only; the whole repo is still indexed.
const EXCL = /(^|\/)(tests?|testing|testdata|spec|specs|fixtures?|examples?|benches|benchmarks?|vendor|node_modules|third_party|playground|docs?|__tests__|deps|extern|external|contrib|generated)(\/|$)|(_test|_spec|\.test|\.spec)\.\w+$|(^|\/)test_[^/]*$|Test[^/]*\.java$/;
// Wrappers whose own first line precedes the doc comment (`template<...>`, `export`, `declare`).
const WRAP = new Set(["template_declaration", "export_statement", "ambient_declaration", "decorated_definition"]);
const ATTR: Record<string, RegExp | undefined> = {
  rust: /^\s*#\[.*\]\s*$/,
  csharp: /^\s*\[.*\]\s*$/,
  scala: /^\s*@\w[\w.]*(\(.*\))?\s*$/,
  typescript: /^\s*@\w[\w.]*(\(.*\))?\s*$/,
};

interface Block { from: number; to: number }
interface Def { name: string; row: number; doc: Block | null; elixirText?: string }

function contiguous(lines: string[], i: number, re: RegExp): Block | null {
  let from = i;
  if (!re.test(lines[i])) return null;
  while (from - 1 >= 0 && re.test(lines[from - 1])) from--;
  return { from, to: i };
}

/** The doc comment ending directly above `row`, or null. Never returns a license header. */
function docBlock(lines: string[], row: number, lang: string): Block | null {
  let i = row - 1;
  const attr = ATTR[lang];
  while (attr && i >= 0 && attr.test(lines[i])) i--;
  if (i < 0) return null;
  let b: Block | null = null;
  if (lang === "rust" || lang === "csharp") b = contiguous(lines, i, /^\s*\/\/\/(?!\/)/);
  else if (lang === "haskell") {
    b = contiguous(lines, i, /^\s*--/);
    if (b) {
      let k = b.to;
      while (k >= b.from && !/^\s*--\s*\|/.test(lines[k])) k--;     // last haddock opener in the run
      b = k >= b.from ? { from: k, to: b.to } : null;
      if (b) for (let j = b.from; j <= b.to; j++) if (/^\s*--\s*\^/.test(lines[j])) { b = null; break; }
    }
  } else {
    const t = lines[i].trim();
    if (t.endsWith("*/")) {
      let j = i;
      while (j >= 0 && !lines[j].includes("/*")) j--;
      if (j >= 0 && lines[j].trimStart().startsWith("/*")) {
        const javadoc = lines[j].trimStart().startsWith("/**");
        if (javadoc || lang === "c" || lang === "cpp") b = { from: j, to: i };
      }
    } else if (lang === "c" || lang === "cpp") b = contiguous(lines, i, /^\s*\/\//);
  }
  if (!b) return null;
  if (/copyright|licen[sc]e|all rights reserved/i.test(lines.slice(b.from, b.to + 1).join("\n"))) return null;
  return b;
}

function outerRow(n: Node): number {
  let x = n;
  while (x.parent && WRAP.has(x.parent.type)) x = x.parent;
  return x.startPosition.row;
}

function walk(root: Node, visit: (n: Node) => void) {
  const stack: Node[] = [root];
  while (stack.length) {
    const n = stack.pop()!;
    visit(n);
    const kids = n.namedChildren;
    for (let i = kids.length - 1; i >= 0; i--) if (kids[i]) stack.push(kids[i]!);
  }
}

const EX_DOC = /^@doc\s+(?:~[sS]\s*)?(?:"""\n?([\s\S]*?)"""|"((?:[^"\\]|\\.)*)")/;

function findDefs(root: Node, lines: string[], lang: string): { defs: Def[]; strip: Block[] } {
  const defs: Def[] = [];
  const strip: Block[] = [];
  walk(root, (n) => {
    if (lang === "elixir") {
      if (n.type === "unary_operator" && /^@(doc|moduledoc|typedoc)\b/.test(n.text)) {
        strip.push({ from: n.startPosition.row, to: n.endPosition.row });
      }
      if (n.type !== "call") return;
      const target = n.childForFieldName("target");
      if (!target || target.type !== "identifier" || !EX_FUNC.has(target.text)) return;
      const argBox = n.namedChildren.find((c) => c?.type === "arguments") ?? null;
      let head = argBox?.namedChildren[0] ?? null;
      if (head?.type === "binary_operator") head = head.childForFieldName("left");
      const name = head?.type === "call" ? head.childForFieldName("target")?.text : head?.type === "identifier" ? head.text : null;
      if (!name) return;
      let s = n.previousNamedSibling, text: string | undefined, blk: Block | null = null;
      while (s && (s.type === "unary_operator" || s.type === "comment")) {
        const m = s.text.match(EX_DOC);
        if (m) { text = (m[1] ?? m[2] ?? "").trim(); blk = { from: s.startPosition.row, to: s.endPosition.row }; break; }
        s = s.previousNamedSibling;
      }
      defs.push({ name, row: n.startPosition.row, doc: blk, elixirText: text });
      return;
    }
    let name: string | null = null, row = n.startPosition.row;
    if (lang === "haskell") {
      if (n.type === "signature" && n.parent?.type === "declarations") {
        const v = n.namedChild(0);
        if (v?.type === "variable") name = v.text;
      } else if (HS_TYPE_DECLS.has(n.type)) {
        name = n.namedChildren.find((c) => c?.type === "name")?.text ?? null;
      }
    } else if (FUNC_TYPES.has(n.type) || CLASS_TYPES.has(n.type)) {
      name = defName(n);
      row = outerRow(n);
    }
    if (!name) return;
    const doc = docBlock(lines, row, lang);
    defs.push({ name, row, doc });
  });
  if (lang !== "elixir") for (const d of defs) if (d.doc) strip.push(d.doc);
  return { defs, strip };
}

/** First sentence of a doc comment as a plain-English query, or null if it is not usable prose. */
function toQuery(rawLines: string[], lang: string, elixirText?: string): string | null {
  let text: string;
  if (lang === "elixir") text = elixirText ?? "";
  else {
    text = rawLines
      .map((l) => l.replace(/^\s*(?:\/\/\/?!?|\/\*\*?|--\s*[|^]?|\*(?!\/))\s?/, "").replace(/\s*\*\/\s*$/, "").trim())
      .join("\n");
  }
  if (lang === "csharp") {
    if (/<inheritdoc/i.test(text)) return null;
    const m = text.match(/<summary>([\s\S]*?)<\/summary>/i);
    if (!m) return null;
    text = m[1];
  }
  text = text
    .replace(/<(?:see|paramref|typeparamref)\s+(?:cref|name|langword)="([^"]+)"\s*\/?>(?:<\/see>)?/gi, "$1")
    .replace(/\{@(?:link|linkplain|code|literal)\s+([^}]*)\}/g, "$1")
    .replace(/\[\[([^\]]+)\]\]/g, "$1")
    .replace(/<[^>]+>/g, " ")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[`*]/g, "");
  const para: string[] = [];
  for (const l of text.split("\n").map((x) => x.trim())) {
    if (!l) { if (para.length) break; else continue; }
    if (/^(@|#|:param|:return|Parameters|Examples?:?|Returns?:?)/.test(l)) { if (para.length) break; else return null; }
    para.push(l);
  }
  let p = para.join(" ").replace(/\s+/g, " ").trim();
  const m = p.match(/^(.+?[.!?])(?=\s+[A-Z(]|$)/);
  if (m) p = m[1];
  p = p.replace(/[.:;,\s]+$/, "");
  if (/^(todo|fixme|deprecated|see |this file|generated|auto-?generated|note[: ])/i.test(p)) return null;
  let words = p.split(" ").filter(Boolean);
  if (words.length < 4) return null;
  if (words.filter((w) => /[A-Za-z]{2,}/.test(w)).length / words.length < 0.7) return null;
  if (words.length > 40) words = words.slice(0, 40);
  return words.join(" ");
}

function walkFiles(dir: string, exts: Record<string, string>, out: string[]) {
  for (const e of readdirSync(dir)) {
    if (e === ".git" || e === "node_modules") continue;
    const p = path.join(dir, e);
    const s = lstatSync(p);
    if (s.isSymbolicLink()) continue;
    if (s.isDirectory()) walkFiles(p, exts, out);
    else if (exts[path.extname(e)] && s.size <= 1_000_000) out.push(p);
  }
}

const [src, lang, outPath, ...rest] = process.argv.slice(2);
if (!src || !lang || !outPath || !LANG_EXTS[lang]) {
  console.error(`usage: extract_docqueries.ts <repoDir> <${Object.keys(LANG_EXTS).join("|")}> <candidates.json> [--strip <dstDir>]`);
  process.exit(1);
}
const stripIdx = rest.indexOf("--strip");
const dst = stripIdx >= 0 ? path.resolve(rest[stripIdx + 1]) : null;
const srcReal = realpathSync(src);   // eval-repos/id-* may be symlinks to earlier clones
const exts = LANG_EXTS[lang];
const files: string[] = [];
walkFiles(srcReal, exts, files);

interface Cand { name: string; file: string; line: number; query: string }
const cands: Cand[] = [];
const stripBy = new Map<string, Block[]>();
let nDefs = 0, nDoc = 0, nFiles = 0;
for (const f of files) {
  const g = exts[path.extname(f)];
  const p = await parserFor(g, f);
  if (!p) continue;
  const text = readFileSync(f, "utf8");
  const tree = p.parse(text);
  if (!tree) continue;
  nFiles++;
  const lines = text.split("\n");
  const rel = path.relative(srcReal, f).split(path.sep).join("/");
  try {
    const { defs, strip } = findDefs(tree.rootNode, lines, g);
    if (strip.length) stripBy.set(f, strip);
    const perName = new Map<string, number>();
    for (const d of defs) perName.set(d.name, (perName.get(d.name) ?? 0) + 1);
    nDefs += defs.length;
    for (const d of defs) {
      if (!d.doc) continue;
      nDoc++;
      if (EXCL.test(rel)) continue;
      // One definition of this name in the file (Elixir: exactly one documented clause), so the file+name label
      // identifies a single definition.
      if (g === "elixir" ? defs.filter((x) => x.name === d.name && x.doc).length !== 1 : perName.get(d.name) !== 1) continue;
      const q = toQuery(lines.slice(d.doc.from, d.doc.to + 1), g, d.elixirText);
      if (q) cands.push({ name: d.name, file: rel, line: d.row + 1, query: q });
    }
  } finally {
    tree.delete();
  }
}
// Identical doc sentences (copy-pasted docs) make the label ambiguous: drop every occurrence.
const seen = new Map<string, number>();
for (const c of cands) seen.set(c.query, (seen.get(c.query) ?? 0) + 1);
const unique = cands.filter((c) => seen.get(c.query) === 1);

let stripped = 0;
if (dst) {
  rmSync(dst, { recursive: true, force: true });
  execFileSync("cp", ["-cR", srcReal, dst]);   // APFS clone: no extra disk for untouched files
  for (const [f, blocks] of stripBy) {
    const drop = new Set<number>();
    for (const b of blocks) for (let r = b.from; r <= b.to; r++) drop.add(r);
    const target = path.join(dst, path.relative(srcReal, f));
    const lines = readFileSync(f, "utf8").split("\n");
    rmSync(target, { force: true });          // break the clone before writing
    writeFileSync(target, lines.filter((_, r) => !drop.has(r)).join("\n"));
    stripped += drop.size;
  }
}
writeFileSync(outPath, JSON.stringify({ repoDir: srcReal, lang, files: nFiles, defs: nDefs, documented: nDoc, candidates: unique }, null, 1));
console.log(`${path.basename(srcReal)} [${lang}]: ${nFiles} files, ${nDefs} definitions, ${nDoc} documented, ${cands.length} usable, ${unique.length} after dedupe` +
  (dst ? `; removed ${stripped} doc-comment lines from ${stripBy.size} files in ${dst}` : ""));
if (!existsSync(outPath)) process.exit(1);
