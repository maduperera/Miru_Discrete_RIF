/**
 * Minimal .env loader (no dependency). Import for its side effect:  `import "../src/dotenv.ts";`
 * Existing process.env values win, so `TAKARA_API_KEY=... npx tsx ...` still overrides the file.
 * The file is gitignored; never print its values.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const file = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", ".env");
if (existsSync(file)) {
  for (const raw of readFileSync(file, "utf-8").split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const eq = line.indexOf("=");
    if (eq < 1) continue;
    const key = line.slice(0, eq).trim();
    const val = line.slice(eq + 1).trim().replace(/^(['"])(.*)\1$/, "$2");
    if (process.env[key] === undefined) process.env[key] = val;
  }
}
