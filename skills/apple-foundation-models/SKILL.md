---
name: apple-foundation-models
description: "Use the `fm` CLI (Apple Foundation Models) for on-device and Private Cloud Compute LLM inference on macOS. Use when the user wants to prompt, chat, serve, or count tokens with Apple's built-in foundation models. Also use for structured output generation (`fm schema`), checking model availability (`fm available`), or checking quota usage (`fm quota-usage`). Trigger on phrases like 'run fm', 'Apple Foundation Model', 'on-device LLM', 'Apple AI', 'fm respond', 'fm chat', 'fm serve', 'fm token-count', 'fm schema', or any task involving Apple's local AI models."
---

# Apple Foundation Models CLI (`fm`)

The `fm` CLI (bundled at `/usr/bin/fm` on macOS) gives access to Apple's on-device and Private Cloud Compute (PCC) foundation models. It supports prompting, interactive chat, OpenAI-compatible serving, token counting, and schema generation.

Two models:
- **`system`** — On-device Apple Foundation Model (default, runs entirely locally)
- **`pcc`** — Apple Foundation Model on Private Cloud Compute (offloads to Apple's secure cloud)

## Subcommands

### `fm respond` — Generate a response

Generate a single response to a prompt. Accepts a prompt argument or reads from stdin.

**Examples:**
```
fm respond 'What is Swift?'
fm respond --model pcc 'Summarize this article'
echo 'Hello' | fm respond
fm respond --image photo.jpg --text 'Describe this image'
```

**Key flags:**
| Flag | Purpose |
|------|---------|
| `-m, --model <model>` | Model to use (`system`, `pcc`; default: `system`) |
| `-i, --instructions <text>` | System instructions / system prompt |
| `--schema <file>` | Path to a JSON schema for structured output |
| `--text <text>` | Additional text segment (repeatable) |
| `--image <path>` | Image file to include (repeatable) |
| `--load-transcript <file>` | Load a previously saved transcript for context |
| `--save-transcript <name>` | Save transcript after responding |
| `--[no-]stream` | Toggle streaming output (default: on) |
| `-g, --greedy` | Greedy sampling (deterministic) |
| `-v, --verbose` | Verbose output |
| **System model only:** | |
| `--use-case <case>` | Model use case (`general`, `content-tagging`) |
| `--guardrails <level>` | Guardrail level (`default`, `permissive-content-transformations`) |

**Output handling:**
- By default, output is streamed to stdout. Pipe to a file or another command as usual.
- Use `--no-stream` to get the full response at once (useful in scripting).
- Use `--verbose` to see token counts, timing, and model info alongside the response.
- Use `--save-transcript <name>` to save the interaction (prompt + response) to `~/.fm/transcripts/` for later reuse with `--load-transcript`.

**Structured output:**
1. First generate a schema with `fm schema object` (see below).
2. Save it to a file (e.g. `schema.json`).
3. Pass it to `fm respond --schema schema.json`. The model will return JSON matching the schema.

When the user needs structured/JSON output, ALWAYS use this two-step approach: generate the schema, write it to a temp file, then pass it with `--schema`.

### `fm chat` — Interactive chat session

Start a persistent, multi-turn chat. Sessions are saved to `~/.fm/sessions/`.

**Examples:**
```
fm chat
fm chat --model pcc --instructions 'You are a coding assistant'
fm chat --resume my-session
fm chat --continue
```

**Key flags:**
| Flag | Purpose |
|------|---------|
| `-m, --model <model>` | Model to use |
| `--set-default-model <m>` | Persist the default model (`system` or `pcc`) |
| `-r, --resume <name>` | Resume a named saved session |
| `--continue` | Continue the most recent session |
| `-i, --instructions <text>` | System instructions |

### `fm serve` — OpenAI-compatible API server

Start a local HTTP server compatible with the OpenAI Chat Completions API format. Useful for integrating Apple Foundation Models into existing tools and scripts that speak the OpenAI protocol.

**Examples:**
```
fm serve                                    # Default: port 8080, localhost only
fm serve --port 1976                        # Custom port
fm serve --host 0.0.0.0 --port 1976         # Listen on all interfaces
fm serve --socket /tmp/fm.sock              # Unix domain socket (recommended for local Python bindings)
```

**Endpoints:**
- `POST /v1/chat/completions` — Chat completions (streaming and non-streaming)
- `GET /v1/models` — List available models
- `GET /health` — Health check

**Key flags:**
| Flag | Purpose |
|------|---------|
| `--host <host>` | Host address to bind (TCP mode) |
| `--port <port>` | Port (1–65535, TCP mode) |
| `--socket <path>` | Unix domain socket path (socket mode) |

The server exposes two model IDs: `system` (on-device) and `pcc` (Private Cloud Compute). The API payload format matches OpenAI's — pass `"model": "system"` or `"model": "pcc"` in the request body.

### `fm token-count` — Count tokens

Count tokens for a prompt, instructions, or existing transcript. Only works with the on-device system model.

**Examples:**
```
fm token-count 'What is Swift?'
fm token-count -i 'Answer concisely' 'What is Swift?'
fm token-count --image photo.jpg --text 'Describe this image'
echo 'Hello' | fm token-count
fm token-count --load-transcript session.json 'Follow up'
```

**Key flags:**
| Flag | Purpose |
|------|---------|
| `-i, --instructions <text>` | Include instruction tokens in count |
| `--text <text>` | Additional text segment (repeatable) |
| `--image <path>` | Image to include (repeatable) |
| `--load-transcript <file>` | Seed the count with a saved transcript |
| `-q, --quiet` | Print only the bare integer count |

**Output notes:**
- In a terminal: `Token count: N`
- When piped: bare integer `N`
- Use `--quiet` to force bare integer output

### `fm schema object` — Generate JSON schema

Generate a JSON schema for structured output from the model. Schemas are used with `fm respond --schema <file>`.

**Syntax:**
```
fm schema object --name <TypeName> [PROPERTY_DECLARATIONS...] [PROPERTY_MODIFIERS...]
```

**Property declarations:**
| Flag | Purpose |
|------|---------|
| `--string <name>` | String property |
| `--integer <name>` | Integer property |
| `--double <name>` | Floating-point property |
| `--boolean <name>` | Boolean property |
| `--object <name>` | Nested object (followed by `--schema`) |
| `--schema <json>` | Provide inline JSON schema (after `--object` or `--anyOf`) |
| `--anyOf` | Build an anyOf union; subsequent `--schema` args become choices |

**Property modifiers (apply to the preceding property):**
| Flag | Purpose |
|------|---------|
| `--array` | Mark preceding property as array of that type |
| `--description <text>` | Set a description on the preceding property |
| `--optional` | Mark the preceding property as optional |

**Common patterns:**

Simple object:
```
fm schema object --name Person --string name --int age --description 'Age in years' --optional
```

Nested objects:
```
fm schema object --name Restaurant --string title \
  --object address --schema "$(fm schema object --name Address --string zipcode)"
```

Union types:
```
fm schema object --name SearchResult --anyOf \
  --schema "$(fm schema object --name Found --string name)" \
  --schema "$(fm schema object --name NotFound --string reason)"
```

Arrays:
```
fm schema object --name Team --string name --string members --array
```

Dot notation for inline nesting:
```
fm schema object --name Order --string customer.name --string customer.email --double total
```

### `fm available` — Check model availability

Check whether the on-device and/or PCC models are available to use.

```
fm available             # Check both
fm available --model system
fm available --model pcc
```

### `fm quota-usage` — Check quota usage

Check how much quota has been used for each model.

```
fm quota-usage           # Check both
fm quota-usage --model system
fm quota-usage --model pcc
```

## Common workflows

### Quick Q&A (on-device)
```
fm respond 'What is the difference between a class and a struct in Swift?'
```

### Multimodal analysis
```
fm respond --image screenshot.png --text 'Describe the UI elements in this screenshot'
```

### Structured data extraction
```bash
# 1. Define the schema
fm schema object --name Product --string name --string price --string availability --optional > /tmp/product_schema.json

# 2. Extract
fm respond --schema /tmp/product_schema.json --image listing.png \
  --instructions 'Extract product info from this image as JSON'
```

### System prompt + streaming + file output
```
fm respond -i 'You are a code reviewer. Be concise.' --no-stream 'Review this code: ...' > review.txt
```

### Local OpenAI-compatible server
```bash
# Start server on port 8080
fm serve --port 8080 &

# Use with curl (or any OpenAI SDK pointed at localhost:8080)
curl http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"system","messages":[{"role":"user","content":"Hello"}]}'
```

### Token budget check before prompting
```bash
TOKENS=$(fm token-count -q 'Long text here...')
echo "Input is $TOKENS tokens"
```

### Chat session with custom instructions
```
fm chat --model pcc --instructions 'You are a SwiftUI expert. Provide minimal, complete examples.'
```

## Limitations & notes

- `fm token-count` only works with the on-device **system** model, not PCC.
- The `--use-case` and `--guardrails` flags apply only to the system (on-device) model.
- The `--image` and `--text` flags accept repeated values: pass each one separately.
- `fm` does not have a `--version` flag.
- Sessions live at `~/.fm/sessions/`; transcripts (from `--save-transcript`) live at `~/.fm/transcripts/`.
- When using `fm serve` with `--socket`, the socket mode is recommended for local Python/script bindings to avoid port conflicts.
- The on-device system model runs entirely locally — no network access required. PCC requires network access to Apple's Private Cloud Compute infrastructure.
