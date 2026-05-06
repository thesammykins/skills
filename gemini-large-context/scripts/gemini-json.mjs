#!/usr/bin/env node
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import process from "node:process";

const DEFAULT_MODEL = "gemini-3.1-pro-preview";
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;

function printJson(value, exitCode = 0) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
  process.exitCode = exitCode;
}

function help() {
  printJson({
    ok: true,
    usage: "node scripts/gemini-json.mjs --prompt <text> [--workdir <dir>] [--model <model>] [--include-dir <dir>] [--schema-file <file>]",
    defaults: {
      model: DEFAULT_MODEL,
      outputFormat: "json",
      approvalMode: "plan",
      timeoutMs: DEFAULT_TIMEOUT_MS,
    },
    options: [
      "--prompt, -p <text>: prompt text",
      "--prompt-file <path>: read prompt from a file",
      "--schema <json-or-text>: append an output schema contract",
      "--schema-file <path>: append an output schema contract from a file",
      "--model, -m <model>: Gemini model or alias",
      "--workdir <path>: working directory for Gemini CLI",
      "--include-dir, --include-directories <path[,path]>: add workspace directories",
      "--timeout-ms <number>: terminate Gemini CLI after this many milliseconds",
      "--skip-trust: pass --skip-trust to Gemini CLI when the caller has intentionally trusted the workspace",
    ],
  });
}

function requireValue(args, index, flag) {
  const value = args[index + 1];
  if (!value || value.startsWith("--")) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function addIncludeDirs(target, value) {
  for (const part of value.split(",")) {
    const trimmed = part.trim();
    if (trimmed) target.push(trimmed);
  }
}

function parseArgs(argv) {
  const parsed = {
    model: DEFAULT_MODEL,
    workdir: process.cwd(),
    includeDirs: [],
    timeoutMs: DEFAULT_TIMEOUT_MS,
    skipTrust: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    switch (arg) {
      case "--help":
      case "-h":
        parsed.help = true;
        break;
      case "--prompt":
      case "-p":
        parsed.prompt = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--prompt-file":
        parsed.promptFile = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--schema":
        parsed.schema = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--schema-file":
        parsed.schemaFile = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--model":
      case "-m":
        parsed.model = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--workdir":
        parsed.workdir = requireValue(argv, i, arg);
        i += 1;
        break;
      case "--include-dir":
      case "--include-directories":
        addIncludeDirs(parsed.includeDirs, requireValue(argv, i, arg));
        i += 1;
        break;
      case "--timeout-ms": {
        const value = Number(requireValue(argv, i, arg));
        if (!Number.isFinite(value) || value <= 0) {
          throw new Error("--timeout-ms must be a positive number");
        }
        parsed.timeoutMs = value;
        i += 1;
        break;
      }
      case "--skip-trust":
        parsed.skipTrust = true;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return parsed;
}

async function readStdinIfAvailable() {
  if (process.stdin.isTTY) return "";

  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

function buildPrompt({ prompt, schema }) {
  const schemaBlock = schema
    ? `\nRequired response schema or shape:\n${schema.trim()}\n`
    : `\nDefault response shape:\n{"ok":true,"summary":"...","findings":[],"evidence":[],"uncertainty":[],"next_steps":[]}\n`;

  return `${prompt.trim()}\n${schemaBlock}\nReturn your final answer as valid JSON only. Do not wrap it in Markdown fences. Do not include prose before or after the JSON. If you cannot complete the task, return {"ok":false,"error":{"kind":"blocked","message":"..."},"findings":[],"evidence":[],"uncertainty":[],"next_steps":[]}.`;
}

function runGemini(geminiArgs, { cwd, timeoutMs }) {
  return new Promise((resolve) => {
    let settled = false;
    let stdout = "";
    let stderr = "";
    let timedOut = false;

    const child = spawn("gemini", geminiArgs, {
      cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });

    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, timedOut, ...result });
    };

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGTERM");
      setTimeout(() => child.kill("SIGKILL"), 5000).unref();
    }, timeoutMs);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      finish({ error, exitCode: null, signal: null });
    });
    child.on("close", (exitCode, signal) => {
      finish({ exitCode, signal, error: null });
    });
  });
}

function parseJson(text, kind) {
  if (text !== null && typeof text === "object") {
    return text;
  }
  if (typeof text !== "string") {
    throw new Error(`${kind} was not a string or object`);
  }
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error(`${kind} was empty`);
  }
  return JSON.parse(trimmed);
}

async function main() {
  let args;
  try {
    args = parseArgs(process.argv.slice(2));
  } catch (error) {
    printJson({ ok: false, error: { kind: "invalid_arguments", message: error.message } }, 2);
    return;
  }

  if (args.help) {
    help();
    return;
  }

  let promptParts = [];
  try {
    if (args.prompt) promptParts.push(args.prompt);
    if (args.promptFile) promptParts.push(await readFile(args.promptFile, "utf8"));
    const stdin = await readStdinIfAvailable();
    if (stdin.trim()) promptParts.push(stdin);

    if (promptParts.length === 0) {
      printJson({ ok: false, error: { kind: "missing_prompt", message: "Provide --prompt, --prompt-file, or stdin." } }, 2);
      return;
    }

    let schema = args.schema ?? "";
    if (args.schemaFile) {
      schema = `${schema}\n${await readFile(args.schemaFile, "utf8")}`.trim();
    }

    const finalPrompt = buildPrompt({ prompt: promptParts.join("\n\n"), schema });
    const geminiArgs = [
      "--model",
      args.model,
      "--prompt",
      finalPrompt,
      "--output-format",
      "json",
      "--approval-mode",
      "plan",
    ];

    if (args.skipTrust) geminiArgs.push("--skip-trust");
    for (const dir of args.includeDirs) {
      geminiArgs.push("--include-directories", dir);
    }

    const result = await runGemini(geminiArgs, { cwd: args.workdir, timeoutMs: args.timeoutMs });

    if (result.error) {
      printJson({
        ok: false,
        error: {
          kind: result.error.code === "ENOENT" ? "gemini_cli_not_found" : "gemini_cli_spawn_failed",
          message: result.error.message,
        },
      }, 1);
      return;
    }

    if (result.timedOut) {
      printJson({
        ok: false,
        error: { kind: "gemini_cli_timeout", message: `Gemini CLI exceeded ${args.timeoutMs}ms.`, signal: result.signal },
        stderr: result.stderr.trim() || undefined,
      }, 1);
      return;
    }

    let envelope;
    try {
      envelope = parseJson(result.stdout, "Gemini CLI JSON output");
    } catch (error) {
      printJson({
        ok: false,
        error: { kind: "gemini_cli_output_not_json", message: error.message, exitCode: result.exitCode },
        stdout: result.stdout.trim() || undefined,
        stderr: result.stderr.trim() || undefined,
      }, 1);
      return;
    }

    if (result.exitCode !== 0 || envelope.error) {
      printJson({
        ok: false,
        error: {
          kind: "gemini_cli_failed",
          message: envelope.error?.message ?? (result.stderr.trim() || "Gemini CLI failed."),
          exitCode: result.exitCode,
          details: envelope.error,
        },
        stats: envelope.stats ?? undefined,
        session_id: envelope.session_id ?? undefined,
      }, 1);
      return;
    }

    let response;
    try {
      response = parseJson(envelope.response, "Gemini response");
    } catch (error) {
      printJson({
        ok: false,
        error: { kind: "model_response_not_json", message: error.message },
        raw_response: envelope.response,
        stats: envelope.stats ?? undefined,
        session_id: envelope.session_id ?? undefined,
      }, 1);
      return;
    }

    printJson({
      ok: true,
      model: args.model,
      response,
      stats: envelope.stats ?? undefined,
      session_id: envelope.session_id ?? undefined,
    });
  } catch (error) {
    printJson({ ok: false, error: { kind: "wrapper_unhandled_error", message: error.message } }, 1);
  }
}

await main();
