#!/usr/bin/env node
import sdk from "@1password/sdk";
import { spawn, execFile as execFileCallback } from "node:child_process";
import { chmod, mkdir, mkdtemp, readFile, rename, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { promisify } from "node:util";

const execFile = promisify(execFileCallback);
const DEFAULT_TOKEN_REF = "op://your-vault/your-item/credential";
const LOAD_TOKEN_SCRIPT = "$HOME/.agents/skills/onepassword-agent/scripts/load-token.zsh";
const DEFAULT_TOKEN_CACHE = path.join(process.env.OP_AGENT_CACHE_DIR || process.env.XDG_RUNTIME_DIR || process.env.TMPDIR || tmpdir(), "onepassword-agent", "op-service-account-token");
const INTEGRATION_NAME = process.env.OP_AGENT_INTEGRATION_NAME || "OpenCode 1Password Agent";
const INTEGRATION_VERSION = process.env.OP_AGENT_INTEGRATION_VERSION || "v1.0.0";
const TOKEN_READ_TIMEOUT_MS = Number(process.env.OP_SERVICE_ACCOUNT_TOKEN_TIMEOUT_MS || 45000);

const HELP = `Usage: op-agent.mjs <command> [options]

Bootstrap once at the start of a new agent/session:
  source "$HOME/.agents/skills/onepassword-agent/scripts/load-token.zsh"

After that, use this Node helper for every 1Password interaction. Do not source the loader before each command; the helper reuses OP_SERVICE_ACCOUNT_TOKEN or the local 0600 token cache.

Commands:
  vaults
  items --vault-id <id>
  item --vault-id <id> --item-id <id>
  validate --ref <op://...>
  run --env NAME=op://... [--env NAME2=op://...] -- <command> [args...]
  pipe --ref <op://...> [--newline] -- <command> [args...]
  secret-file --ref <op://...> [--env NAME] -- <command> [args...]
  set-field --vault-id <id> --item-id <id> --field-id <id> (--value-ref <op://...>|--value-env <name>|--value-file <path>|--value-stdin|--value-generate random|memorable|pin)
  create-login --vault-id <id> --title <title> (--username-ref <op://...>|--username-env <name>|--username-file <path>) (--password-ref <op://...>|--password-env <name>|--password-file <path>|--password-generate random|memorable|pin) [--website <url>] [--tag <tag>]
  archive --vault-id <id> --item-id <id>

Global option:
  --token-ref <op://...>  Override OP_SERVICE_ACCOUNT_TOKEN_REF for this process.
  --bootstrap-token       Fallback only: read the service account token with op CLI if env/cache is missing.
`;

function fail(message, code = 1) {
  process.stderr.write(`${message}\n`);
  process.exit(code);
}

function parseFlags(args, booleanFlags = new Set(), repeatFlags = new Set()) {
  const options = {};
  const positionals = [];

  for (let i = 0; i < args.length; i += 1) {
    const token = args[i];
    if (!token.startsWith("--")) {
      positionals.push(token);
      continue;
    }

    const key = token.slice(2);
    if (booleanFlags.has(key)) {
      options[key] = true;
      continue;
    }

    const value = args[i + 1];
    if (value === undefined) {
      fail(`Missing value for --${key}`, 2);
    }
    i += 1;

    if (repeatFlags.has(key)) {
      options[key] ||= [];
      options[key].push(value);
    } else {
      options[key] = value;
    }
  }

  return { options, positionals };
}

function splitCommand(args) {
  const separator = args.indexOf("--");
  if (separator === -1) {
    return { optionArgs: args, commandArgs: [] };
  }
  return {
    optionArgs: args.slice(0, separator),
    commandArgs: args.slice(separator + 1),
  };
}

function requireOption(options, key) {
  const value = options[key];
  if (!value) {
    fail(`Missing required option --${key}`, 2);
  }
  return value;
}

function printJson(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

async function readTokenFromReference(tokenRef) {
  try {
    const { stdout } = await execFile("op", ["read", tokenRef], {
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
      timeout: TOKEN_READ_TIMEOUT_MS,
      killSignal: "SIGTERM",
    });
    const token = stdout.trim();
    if (!token) {
      fail("1Password returned an empty service account token.");
    }
    return token;
  } catch (error) {
    const detail = error.code === "ENOENT"
      ? "1Password CLI 'op' was not found."
      : error.killed
        ? "Timed out waiting for 1Password CLI to read the token reference."
        : "1Password CLI could not read the token reference.";
    fail(`${detail}\nLoad it into your current shell first with:\n  source \"${LOAD_TOKEN_SCRIPT}\"`);
  }
}

async function readCachedToken() {
  const cachePath = process.env.OP_SERVICE_ACCOUNT_TOKEN_CACHE || DEFAULT_TOKEN_CACHE;
  try {
    const token = (await readFile(cachePath, "utf8")).trim();
    return token || undefined;
  } catch (error) {
    if (error.code === "ENOENT") return undefined;
    throw error;
  }
}

async function writeCachedToken(token) {
  if (!token || process.env.OP_AGENT_DISABLE_TOKEN_CACHE === "1") return;
  const cachePath = process.env.OP_SERVICE_ACCOUNT_TOKEN_CACHE || DEFAULT_TOKEN_CACHE;
  const dir = path.dirname(cachePath);
  const tempDir = await mkdtemp(path.join(tmpdir(), "op-agent-cache-"));
  const tempPath = path.join(tempDir, "token");
  try {
    await mkdir(dir, { recursive: true, mode: 0o700 });
    await writeFile(tempPath, token, { mode: 0o600 });
    await chmod(tempPath, 0o600);
    await rename(tempPath, cachePath);
    await chmod(cachePath, 0o600);
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

async function ensureToken(globalOptions) {
  const tokenRef = globalOptions["token-ref"] || process.env.OP_SERVICE_ACCOUNT_TOKEN_REF || DEFAULT_TOKEN_REF;
  if (process.env.OP_SERVICE_ACCOUNT_TOKEN) {
    await writeCachedToken(process.env.OP_SERVICE_ACCOUNT_TOKEN);
    return process.env.OP_SERVICE_ACCOUNT_TOKEN;
  }

  const cachedToken = await readCachedToken();
  if (cachedToken) {
    process.env.OP_SERVICE_ACCOUNT_TOKEN = cachedToken;
    process.env.OP_SERVICE_ACCOUNT_TOKEN_REF = tokenRef;
    return cachedToken;
  }

  if (!globalOptions["bootstrap-token"] && process.env.OP_AGENT_BOOTSTRAP_TOKEN !== "1") {
    fail(`OP_SERVICE_ACCOUNT_TOKEN is not loaded and no local token cache was found. Bootstrap once, then rerun the helper:\n  source "${LOAD_TOKEN_SCRIPT}"\nAfter bootstrap, run node ${process.argv[1]} ... for all further interactions. Use --bootstrap-token only for a one-off fallback; it may trigger 1Password CLI auth.`);
  }

  const token = await readTokenFromReference(tokenRef);
  process.env.OP_SERVICE_ACCOUNT_TOKEN = token;
  process.env.OP_SERVICE_ACCOUNT_TOKEN_REF = tokenRef;
  await writeCachedToken(token);
  return token;
}

async function createClient(globalOptions) {
  const token = await ensureToken(globalOptions);
  return sdk.createClient({
    auth: token,
    integrationName: INTEGRATION_NAME,
    integrationVersion: INTEGRATION_VERSION,
  });
}

function redactedField(field) {
  return {
    id: field.id,
    title: field.title,
    sectionId: field.sectionId || field.section_id,
    fieldType: field.fieldType || field.field_type,
    purpose: field.purpose,
    hasValue: Boolean(field.value),
    value: field.value ? "[redacted]" : undefined,
    detailsType: field.details?.type,
  };
}

function redactedItem(item) {
  return {
    id: item.id,
    title: item.title,
    category: item.category,
    vaultId: item.vaultId,
    state: item.state,
    tags: item.tags,
    websites: item.websites,
    sections: item.sections,
    fields: (item.fields || []).map(redactedField),
    files: (item.files || []).map((file) => ({
      name: file.attributes?.name,
      sectionId: file.sectionId,
      fieldId: file.fieldId,
    })),
    document: item.document
      ? { name: item.document.name, size: item.document.size, id: item.document.id }
      : undefined,
  };
}

async function resolveSecret(client, ref) {
  if (!ref.startsWith("op://")) {
    fail(`Expected a 1Password secret reference, got: ${ref}`, 2);
  }
  return client.secrets.resolve(ref);
}

function redactText(text, secrets) {
  let result = text;
  for (const secret of secrets) {
    if (secret) {
      result = result.split(secret).join("[REDACTED]");
    }
  }
  return result;
}

function runChild(commandArgs, envAdd, secrets, stdinValue) {
  if (commandArgs.length === 0) {
    fail("Missing command after --", 2);
  }

  return new Promise((resolve) => {
    const child = spawn(commandArgs[0], commandArgs.slice(1), {
      env: { ...process.env, ...envAdd },
      stdio: [stdinValue === undefined ? "inherit" : "pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      stderr += `${error.message}\n`;
    });
    child.on("close", (code, signal) => {
      if (stdout) process.stdout.write(redactText(stdout, secrets));
      if (stderr) process.stderr.write(redactText(stderr, secrets));
      if (signal) {
        process.stderr.write(`Command exited from signal ${signal}\n`);
        resolve(1);
      } else {
        resolve(code ?? 1);
      }
    });

    if (stdinValue !== undefined) {
      child.stdin.end(stdinValue);
    }
  });
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

function parseBool(value, defaultValue) {
  if (value === undefined) return defaultValue;
  if (["1", "true", "yes", "on"].includes(String(value).toLowerCase())) return true;
  if (["0", "false", "no", "off"].includes(String(value).toLowerCase())) return false;
  fail(`Invalid boolean value: ${value}`, 2);
}

function generatedPassword(mode, options, prefix) {
  const length = Number(options[`${prefix}-length`] || options.length || (mode === "pin" ? 8 : 32));
  if (!Number.isInteger(length) || length <= 0) {
    fail("Password length must be a positive integer.", 2);
  }

  if (mode === "pin") {
    return sdk.Secrets.generatePassword({ type: "Pin", parameters: { length } });
  }
  if (mode === "memorable") {
    return sdk.Secrets.generatePassword({
      type: "Memorable",
      parameters: {
        separatorType: sdk.SeparatorType.Hyphens,
        capitalize: parseBool(options[`${prefix}-capitalize`] || options.capitalize, true),
        wordListType: sdk.WordListType.FullWords,
        wordCount: Number(options[`${prefix}-words`] || options.words || 4),
      },
    });
  }
  if (mode === "random") {
    return sdk.Secrets.generatePassword({
      type: "Random",
      parameters: {
        includeDigits: parseBool(options[`${prefix}-digits`] || options.digits, true),
        includeSymbols: parseBool(options[`${prefix}-symbols`] || options.symbols, true),
        length,
      },
    });
  }
  fail(`Unsupported password generation mode: ${mode}`, 2);
}

async function resolveSource(client, options, prefix) {
  const sources = [
    `${prefix}-ref`,
    `${prefix}-env`,
    `${prefix}-file`,
    `${prefix}-stdin`,
    `${prefix}-generate`,
  ].filter((key) => options[key]);

  if (sources.length !== 1) {
    fail(`Specify exactly one source for ${prefix}.`, 2);
  }

  if (options[`${prefix}-ref`]) return resolveSecret(client, options[`${prefix}-ref`]);
  if (options[`${prefix}-env`]) {
    const name = options[`${prefix}-env`];
    if (!(name in process.env)) fail(`Environment variable ${name} is not set.`, 2);
    return process.env[name];
  }
  if (options[`${prefix}-file`]) return readFile(options[`${prefix}-file`], "utf8");
  if (options[`${prefix}-stdin`]) return readStdin();
  return generatedPassword(options[`${prefix}-generate`], options, prefix);
}

async function commandVaults(client) {
  const vaults = await client.vaults.list();
  printJson(vaults.map((vault) => ({ id: vault.id, title: vault.title, description: vault.description })));
}

async function commandItems(client, args) {
  const { options } = parseFlags(args);
  const vaultId = requireOption(options, "vault-id");
  const items = await client.items.list(vaultId);
  printJson(items.map((item) => ({ id: item.id, title: item.title, category: item.category, state: item.state, vaultId: item.vaultId })));
}

async function commandItem(client, args) {
  const { options } = parseFlags(args);
  const vaultId = requireOption(options, "vault-id");
  const itemId = requireOption(options, "item-id");
  const item = await client.items.get(vaultId, itemId);
  printJson(redactedItem(item));
}

async function commandValidate(args) {
  const { options } = parseFlags(args);
  const ref = requireOption(options, "ref");
  sdk.Secrets.validateSecretReference(ref);
  printJson({ valid: true, ref });
}

async function commandRun(client, args) {
  const { optionArgs, commandArgs } = splitCommand(args);
  const { options } = parseFlags(optionArgs, new Set(), new Set(["env"]));
  const envSpecs = options.env || [];
  const envAdd = {};
  const secrets = [];

  for (const spec of envSpecs) {
    const split = spec.indexOf("=");
    if (split <= 0) fail(`Invalid --env value ${spec}; expected NAME=op://...`, 2);
    const name = spec.slice(0, split);
    const ref = spec.slice(split + 1);
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) fail(`Invalid environment variable name: ${name}`, 2);
    const secret = await resolveSecret(client, ref);
    envAdd[name] = secret;
    secrets.push(secret);
  }

  process.exit(await runChild(commandArgs, envAdd, secrets));
}

async function commandPipe(client, args) {
  const { optionArgs, commandArgs } = splitCommand(args);
  const { options } = parseFlags(optionArgs, new Set(["newline"]));
  const secret = await resolveSecret(client, requireOption(options, "ref"));
  const stdinValue = options.newline ? `${secret}\n` : secret;
  process.exit(await runChild(commandArgs, {}, [secret], stdinValue));
}

async function commandSecretFile(client, args) {
  const { optionArgs, commandArgs } = splitCommand(args);
  const { options } = parseFlags(optionArgs);
  const secret = await resolveSecret(client, requireOption(options, "ref"));
  const envName = options.env || "OP_SECRET_FILE";
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(envName)) fail(`Invalid environment variable name: ${envName}`, 2);

  const dir = await mkdtemp(path.join(tmpdir(), "op-agent-"));
  const filePath = path.join(dir, "secret");
  try {
    await writeFile(filePath, secret, { mode: 0o600 });
    await chmod(filePath, 0o600);
    process.exitCode = await runChild(commandArgs, { [envName]: filePath }, [secret, filePath]);
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

async function commandSetField(client, args) {
  const { options } = parseFlags(args, new Set(["value-stdin"]));
  const vaultId = requireOption(options, "vault-id");
  const itemId = requireOption(options, "item-id");
  const fieldId = requireOption(options, "field-id");
  const value = await resolveSource(client, options, "value");
  const item = await client.items.get(vaultId, itemId);
  let found = false;
  const fields = item.fields.map((field) => {
    if (field.id === fieldId) {
      found = true;
      return { ...field, value };
    }
    return field;
  });

  if (!found) fail(`Field ${fieldId} was not found on item ${itemId}.`, 2);
  const updated = await client.items.put({ ...item, fields });
  printJson({ updated: true, vaultId: updated.vaultId, itemId: updated.id, title: updated.title, fieldId });
}

async function commandCreateLogin(client, args) {
  const { options } = parseFlags(args, new Set(), new Set(["website", "tag"]));
  const vaultId = requireOption(options, "vault-id");
  const title = requireOption(options, "title");
  const username = await resolveSource(client, options, "username");
  const password = await resolveSource(client, options, "password");
  const websites = (options.website || []).map((url) => ({
    url,
    label: "website",
    autofillBehavior: sdk.AutofillBehavior.AnywhereOnWebsite,
  }));

  const item = await client.items.create({
    title,
    category: sdk.ItemCategory.Login,
    vaultId,
    fields: [
      { id: "username", title: "username", fieldType: sdk.ItemFieldType.Text, value: username },
      { id: "password", title: "password", fieldType: sdk.ItemFieldType.Concealed, value: password },
    ],
    tags: options.tag || [],
    websites,
  });

  printJson({ created: true, vaultId: item.vaultId, itemId: item.id, title: item.title, fields: ["username", "password"] });
}

async function commandArchive(client, args) {
  const { options } = parseFlags(args);
  const vaultId = requireOption(options, "vault-id");
  const itemId = requireOption(options, "item-id");
  await client.items.archive(vaultId, itemId);
  printJson({ archived: true, vaultId, itemId });
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0 || argv.includes("--help") || argv.includes("-h")) {
    process.stdout.write(HELP);
    return;
  }

  const globalOptions = {};
  while (argv[0]?.startsWith("--")) {
    const key = argv.shift().slice(2);
    if (key === "token-ref") {
      globalOptions[key] = argv.shift();
      if (!globalOptions[key]) fail("Missing value for --token-ref", 2);
    } else if (key === "bootstrap-token") {
      globalOptions[key] = true;
    } else {
      fail(`Unknown global option: --${key}`, 2);
    }
  }

  const command = argv.shift();
  if (command === "validate") {
    await ensureToken(globalOptions);
    return commandValidate(argv);
  }

  const client = await createClient(globalOptions);
  if (command === "vaults") return commandVaults(client);
  if (command === "items") return commandItems(client, argv);
  if (command === "item") return commandItem(client, argv);
  if (command === "run") return commandRun(client, argv);
  if (command === "pipe") return commandPipe(client, argv);
  if (command === "secret-file") return commandSecretFile(client, argv);
  if (command === "set-field") return commandSetField(client, argv);
  if (command === "create-login") return commandCreateLogin(client, argv);
  if (command === "archive") return commandArchive(client, argv);

  fail(`Unknown command: ${command}`, 2);
}

main().catch((error) => {
  process.stderr.write(`${error.message || error}\n`);
  process.exit(1);
});
