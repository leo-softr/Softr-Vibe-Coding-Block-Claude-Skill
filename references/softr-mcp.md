# Softr MCP Server

The official Softr MCP server (`https://mcp.softr.io/mcp`) gives an AI assistant (Claude Code, Claude Desktop, claude.ai, Cursor, ChatGPT, Mistral) direct access to a Softr **workspace**: databases, applications, vibe coding blocks, integrations (external data sources), and workflows. On this workspace server, everything the assistant does happens as the connected user, with their permissions, and shows up in Studio like any other change.

**There are now TWO server classes.** Besides the workspace server above, Softr ships **per-application MCP servers** — one server per published app, exposing that app's data (and only what the app's pages actually use) through the app's own permission model. Different tools, different schema doc, and (apparently) a different identity model. See [Per-application MCP servers](#per-application-mcp-servers). (Live-enumerated 2026-08-31; roster facts below marked "roster-verified" mean the tool exists — its behavior was not necessarily exercised.)

**This file is a sibling concern to the [../datasources/](../datasources/) guides, which cover in-block data fetching (`useRecords` + `q.select()`).** The MCP runs at chat-build time, not inside the block. For Vibe Coding work it matters twice: it answers "what fields does this table have?" without any paste-ins, and it can create and deploy the block itself — no copy-paste into Studio.

> Historical note: this file was previously named `softr-database-mcp.md` and described a databases-only server with granular scopes. That server has since grown into the workspace-wide MCP documented here; the old "does NOT cover external sources" limitation is gone (see [Integrations](#browsing-integrations-external-data-sources)).

> **The workspace server's tools were renamed on 2026-10-01** — noun first: `get_vibe_coding_block_code` is now `vibe_coding_block_get_code`, `publish_app` is `application_publish`, `get_schema` is `database_get_field_reference`. This file uses the new names throughout. Notes, prompts or scripts written before then use the old ones; translate them with the [old → new map](#tool-names--the-2026-10-01-rename). The Workflows tools kept their names, and the per-application servers are a separate tool set — `list_tables`, `get_record`, `update_record` and `get_schema` there are NOT the old workspace tools.

## Contents

- [What it covers](#what-it-covers)
- [Tool names — the 2026-10-01 rename](#tool-names--the-2026-10-01-rename)
- [Connection and auth](#connection-and-auth)
- [Permissions model](#permissions-model)
- [Vibe coding block tools](#vibe-coding-block-tools) — incl. [what the server enforces on a block's data endpoints](#what-the-server-enforces-on-a-blocks-data-endpoints)
- [Adopting Studio-AI-generated code](#adopting-studio-ai-generated-code)
- [Vibe coding gotchas (official)](#vibe-coding-gotchas-official)
- [Application management tools](#application-management-tools) — incl. [testing as any user via "Preview as"](#testing-as-any-app-user-without-logins--the-preview-as-switcher)
- [Browsing integrations (external data sources)](#browsing-integrations-external-data-sources)
- [Softr Database tools](#softr-database-tools)
- [Workflows](#workflows)
- [Per-application MCP servers](#per-application-mcp-servers)
- [Two delivery paths for this skill](#two-delivery-paths-for-this-skill)
- [When the MCP is not installed](#when-the-mcp-is-not-installed)

## What it covers

| Area | What the assistant can do | Official docs |
|---|---|---|
| Databases | Query, filter, aggregate; create/update **and delete** records; build **and delete** tables, fields, databases | https://docs.softr.io/mcp/databases |
| Applications | **Create whole apps**; manage app users and login settings; swap an app's data source; read apps, pages, blocks, permissions, user groups; preview; publish — see [Application management tools](#application-management-tools) | https://docs.softr.io/mcp/apps |
| Vibe coding blocks | Create and edit blocks, manage settings, visibility, versions, data source connections | https://docs.softr.io/mcp/vibe-coding |
| Integrations | Browse external data sources connected to the workspace, down to field level | https://docs.softr.io/mcp/integrations |
| Workflows | Build, wire, test, and publish workflows — 28 tools and a 418-node trigger/action catalog; see [Workflows](#workflows) | https://docs.softr.io/mcp/workflows |

`workspace_list` is often the first call — it turns "my Sales workspace" into the workspace ID every other tool needs. The server's own instructions now start from `application_list` (applications and their workspace IDs) and `database_list` (databases), and keep `workspace_list` for turning a workspace name into an ID.

## Tool names — the 2026-10-01 rename

On 2026-10-01 Softr renamed the workspace-server tools outside Workflows to **area first, then verb**:
`vibe_coding_block_*`, `application_*` (pages are `application_page_*`), `database_*`,
`integration_*` and `workspace_*`. 79 tools were renamed and one was added
(`application_update_pwa_settings`); the 28 Workflows tools and `get_workspace_integrations` kept their names. The
map below was checked against the tool lists the server delivered on 2026-09-30 (old) and 2026-10-01 (new).

**The Workflows tools have since followed** (when exactly is not known; first seen 2026-10-05). The 2026-10-05 roster delivered all 28 as `workflow_*`:
`workflow_create`, `workflow_get`, `workflow_list`, `workflow_publish`, `workflow_update_node_inputs`,
`workflow_get_node_specifications`, `workflow_list_node_types`, `workflow_test_node` and the rest,
i.e. area first, then the old verb and object. [Workflows](#workflows) below uses the new names
(re-checked against the live roster 2026-10-06: all 28 present). That roster had no `get_workspace_integrations`;
`integration_list` covers it.

Most new names are the old words reordered. These are the ones you would not guess:

| Old | New |
|---|---|
| `get_schema` | `database_get_field_reference` |
| `aggregate_data` | `database_aggregate_records` |
| `get_access_control` | `application_get_access_overview` |
| `search_databases` | `database_search` |
| `list_integrations` (earlier `list_data_sources`) | `integration_list` |
| `list_data_source_databases` / `_schemas` / `_tables` / `_table_fields` | `integration_list_databases` / `_schemas` / `_tables` / `_table_fields` |
| `get_page`, `get_block`, `list_pages`, `create_page`, `get_page_permissions` | `application_page_get`, `application_page_get_block`, `application_page_list`, `application_page_create`, `application_page_get_permissions` |
| `preview_app`, `publish_app` | `application_preview`, `application_publish` |
| `create_database`, `get_database`, `list_databases`, `update_database`, `delete_database` | `database_create`, `database_get`, `database_list`, `database_update`, `database_delete` |

<details>
<summary>Full old → new map (79 tools)</summary>

| Area | Old | New |
|---|---|---|
| Vibe coding blocks | `get_vibe_coding_docs` | `vibe_coding_block_get_docs` |
| | `create_vibe_coding_block` | `vibe_coding_block_create` |
| | `delete_vibe_coding_block` | `vibe_coding_block_delete` |
| | `get_vibe_coding_block_code` | `vibe_coding_block_get_code` |
| | `get_vibe_coding_block_settings` | `vibe_coding_block_get_settings` |
| | `update_vibe_coding_block_code` | `vibe_coding_block_update_code` |
| | `update_vibe_coding_block_code_search_replace` | `vibe_coding_block_update_code_search_replace` |
| | `update_vibe_coding_block_settings` | `vibe_coding_block_update_settings` |
| | `set_vibe_coding_block_visibility` | `vibe_coding_block_set_visibility` |
| | `set_vibe_coding_block_action_visibility` | `vibe_coding_block_set_action_visibility` |
| | `list_vibe_coding_block_versions` | `vibe_coding_block_list_versions` |
| | `restore_vibe_coding_block_version` | `vibe_coding_block_restore_version` |
| | `duplicate_vibe_coding_block_from_version` | `vibe_coding_block_duplicate_from_version` |
| | `connect_vibe_coding_block_data_source` | `vibe_coding_block_connect_data_source` |
| | `disconnect_vibe_coding_block_data_source` | `vibe_coding_block_disconnect_data_source` |
| | `set_vibe_coding_block_data_source_sort` | `vibe_coding_block_set_data_source_sort` |
| | `set_vibe_coding_block_data_source_record_filters` | `vibe_coding_block_set_data_source_record_filters` |
| Applications | `list_applications` | `application_list` |
| | `get_application` | `application_get` |
| | `create_application` | `application_create` |
| | `set_application_name` | `application_set_name` |
| | `set_application_subdomain` | `application_set_subdomain` |
| | `set_application_domain` | `application_set_domain` |
| | `set_application_login` | `application_set_login` |
| | `configure_application_sign_up` | `application_configure_sign_up` |
| | `configure_application_email_sender` | `application_configure_email_sender` |
| | `update_application_data_source` | `application_update_data_source` |
| | `get_access_control` | `application_get_access_overview` |
| | `list_application_users` | `application_list_users` |
| | `add_application_user` | `application_add_user` |
| | `remove_application_user` | `application_remove_user` |
| | `set_application_user_activation` | `application_set_user_activation` |
| | `list_user_groups` | `application_list_user_groups` |
| | `create_user_group` | `application_create_user_group` |
| | `update_user_group` | `application_update_user_group` |
| | `delete_user_group` | `application_delete_user_group` |
| | `create_user_connection` | `application_create_user_connection` |
| | `get_user_connection` | `application_get_user_connection` |
| | `remove_user_connection` | `application_remove_user_connection` |
| | `list_pages` | `application_page_list` |
| | `get_page` | `application_page_get` |
| | `create_page` | `application_page_create` |
| | `get_block` | `application_page_get_block` |
| | `get_page_permissions` | `application_page_get_permissions` |
| | `preview_app` | `application_preview` |
| | `publish_app` | `application_publish` |
| | *(new)* | `application_update_pwa_settings` |
| Databases | `list_databases` | `database_list` |
| | `search_databases` | `database_search` |
| | `get_database` | `database_get` |
| | `create_database` | `database_create` |
| | `update_database` | `database_update` |
| | `delete_database` | `database_delete` |
| | `get_schema` | `database_get_field_reference` |
| | `list_tables` | `database_list_tables` |
| | `get_table` | `database_get_table` |
| | `create_table` | `database_create_table` |
| | `update_table` | `database_update_table` |
| | `delete_table` | `database_delete_table` |
| | `list_fields` | `database_list_fields` |
| | `create_field` | `database_create_field` |
| | `update_field` | `database_update_field` |
| | `delete_field` | `database_delete_field` |
| | `list_views` | `database_list_views` |
| | `list_records` | `database_list_records` |
| | `search_records` | `database_search_records` |
| | `get_record` | `database_get_record` |
| | `create_record` | `database_create_record` |
| | `create_records` | `database_create_records` |
| | `update_record` | `database_update_record` |
| | `delete_record` | `database_delete_record` |
| | `delete_records` | `database_delete_records` |
| | `aggregate_data` | `database_aggregate_records` |
| Integrations | `list_integrations` | `integration_list` |
| | `list_data_source_databases` | `integration_list_databases` |
| | `list_data_source_schemas` | `integration_list_schemas` |
| | `list_data_source_tables` | `integration_list_tables` |
| | `list_data_source_table_fields` | `integration_list_table_fields` |
| Workspace | `list_workspaces` | `workspace_list` |
| | `list_workspace_email_senders` | `workspace_list_email_senders` |

</details>

**Per-application servers are a different tool set, and are not covered by this map.** Their
`list_tables`, `get_record`, `create_record`, `update_record`, `delete_record` and `get_schema` share
names with the old workspace tools but belong to [those servers](#per-application-mcp-servers). When
translating an old note, check which server a call went to before renaming it.

## Connection and auth

- **Server URL:** `https://mcp.softr.io/mcp` (streamable HTTP)
- **Official docs:** https://docs.softr.io/mcp/overview

Install in Claude Code:

```bash
claude mcp add --transport http softr https://mcp.softr.io/mcp
```

Then start a new session and run `/mcp` to complete OAuth in the browser.

Two auth methods:

1. **OAuth (recommended)** — pre-built clients exist for Claude (claude.ai), Cursor, ChatGPT, and Mistral. If a Client ID is requested, use the value from the [overview docs](https://docs.softr.io/mcp/overview); leave Client Secret blank (Softr's OAuth clients are public). The assistant cannot request permissions — the user always picks them on Softr's authorization screen.
2. **Personal access token** — for custom clients. Created in Softr under **Settings → API tokens** (name, expiry, workspace + permission scoping), then used as a Bearer token.

Revoke or edit access anytime in **Settings → API tokens** (Authorized apps section for OAuth, token list for PATs).

## Permissions model

Permissions are chosen per workspace across **three areas with bundled levels** — not granular per-tool scopes. Each level includes everything below it (no "write without read").

| Area | Levels | Highest level adds |
|---|---|---|
| Applications & Forms | Full access · Read only · None | Creating/editing vibe coding blocks, previewing, publishing |
| Databases | Full access · Edit data · View only · None | Schema changes (tables/fields); Edit data adds record writes |
| Workflows | Full access · Read only · None | Building, testing, publishing workflows |

For block-building work you need **Applications & Forms: Full access** (to create/edit blocks) plus at least **Databases: View only** (schema discovery). Integrations browsing rides on Applications & Forms read access.

## Vibe coding block tools

Before writing any block code through the MCP, call `vibe_coding_block_get_docs` — it returns the current version of the [Vibe Coding Developer Guide](https://docs.softr.io/vibe-coding-developer-guide), which is the authority on hook signatures if it and this skill ever disagree. On runtime *behaviour* the guide's prose can lag a live capture, and where it does this skill says so: the guide still describes `useRecords({ enabled })` as a way to defer loading (checked 2026-10-06), while a 2026-09-18 network capture showed `useRecords` fetching anyway ([reading.md](../datasources/reading.md#userecords-ignores-enabled-false)). Trust the capture until a newer one says otherwise.

| Group | Tools |
|---|---|
| Create / read | `vibe_coding_block_get_docs`, `vibe_coding_block_create`, `vibe_coding_block_get_code`, `vibe_coding_block_get_settings` |
| Edit code | `vibe_coding_block_update_code` (full replace), `vibe_coding_block_update_code_search_replace` (targeted edit) |
| Settings / visibility | `vibe_coding_block_update_settings`, `vibe_coding_block_set_visibility`, `vibe_coding_block_set_action_visibility` |
| Versions | `vibe_coding_block_list_versions`, `vibe_coding_block_restore_version`, `vibe_coding_block_duplicate_from_version` |
| Data sources | `vibe_coding_block_connect_data_source`, `vibe_coding_block_disconnect_data_source`, `vibe_coding_block_set_data_source_sort`, `vibe_coding_block_set_data_source_record_filters` |
| Any block | `application_page_get_block` (roster-verified 2026-08-31; presumed to read any block type, not just vibe blocks — unconfirmed by a live call on a native block) |

Editable settings via MCP are the same fields as the block's **Content → Settings** panel; sort and record filters are the same as the **Source** tab. Duplicating from a version is the safe way to try an alternative — the original keeps working while you experiment on the copy.

**Which read to use** (from the tools' own descriptions, 2026-10-01):

- `vibe_coding_block_get_settings` returns the block's settings, its `actions` (type, `dataSourceId`,
  mapped fields, `permission`, `isDefaultVisibility`) and its wired `dataSources` — everything except
  the source. It is the cheap read before any permission, sort, filter or settings change, and for
  checking what a restore or duplicate kept.
- `vibe_coding_block_get_code` adds the source. Its `dataSources` list is the only reliable answer to
  "is a datasource actually wired to this block?" — the compiler never sees the wiring — and each entry's
  `fieldReferenceKey` (`id` or `name`) says how that source's fields must be referenced in `q.select()`.
- `vibe_coding_block_get_code` with **`includeCode: false`** skips the source text but still returns
  `sourceSha256` and `sourceBytes` — about 1 KB however large the block is. Use it to [verify a
  push](#verifying-a-push--the-deployed-source-is-the-only-proof) (verified live 2026-10-01).
- Push results now report `sourceSha256` and `sourceBytes` too, for the source Softr actually stored.

### Which edit tool: full replace vs. targeted search-replace

`vibe_coding_block_update_code` sends the whole file; `vibe_coding_block_update_code_search_replace`
sends only the fragments that change. This is not just a bandwidth choice — it changes what can go wrong.

**Reach for search-replace when ONE source file is deployed to SEVERAL blocks.** Datasource UUIDs are
per BLOCK, not per table, so a file living on two pages needs a different `datasource.define()` pair in
each. A full replace overwrites that pair and forces a manual swap on every single push — the classic
way to point a project page at the company page's data. Targeted replacements never touch lines you did
not name, so **each block keeps its own pair and the swap step disappears entirely** (verified
2026-09-09 across a report block deployed to two pages). It is also the safer option on large files:
retransmitting ~100KB verbatim to change one class string is its own corruption risk.

**Search-replace on a 100KB+ block — the working recipe (verified live 2026-09-18).** Sent a real
array of `{ search, replace }` objects (not a JSON string — see
[the array-argument rejection](#the-array-argument-rejection-and-why-it-is-a-security-issue)), the
tool patches large blocks reliably, and nothing but the fragments passes through the model's
context. Keep the local mirror in step mechanically rather than by hand:

1. Prove deployed == disk first ([below](#verifying-a-push--the-deployed-source-is-the-only-proof)).
2. Write the ops once, as data. Send them to the tool, and apply the **identical** ops to the local
   mirror with a script that asserts each `search` occurs exactly once before replacing it.
3. Several rounds of ops are fine — **verify once at the end**: compare the `sourceSha256` of the
   last push result with the mirror's SHA-256. A mismatch means an op landed differently on one
   side. The digest describes the source Softr stored after merging your edits, not the edits you
   sent, which is what makes it usable here: on this path you never see the merged file yourself.

One encoding trap: JSON `\uXXXX` escapes inside the ops are **decoded to the real characters** on
Softr's side (`"\u2014"` is stored as `—`). The mirror must therefore hold raw UTF-8 — apply the
ops to it *after* JSON-decoding them, never as the escaped text, or the final comparison
fails on every non-ASCII character.
The same decoding happens to an agent's own tool-call arguments: a `\u2014` typed into a
file-writing tool lands on disk as `—` (it put a wrong example into this very paragraph
twice, 2026-09-18 and 2026-10-06). When a file must hold a literal backslash-u sequence, build the
backslash at runtime (`chr(92)` in Python) and check the bytes afterwards.

**Reach for the full replace when the change is structural** — reordering JSX, moving logic between
components, adding a hook — where being sure of "the exact current text" of a dozen scattered fragments
is harder than being sure of the whole file. Also use it when the local file is the source of truth and
has drifted from the deployed block in ways you have not enumerated.

### Verifying a push — the deployed source is the only proof

`vibe_coding_block_update_code` returning `errors: null, warnings: null` proves the code **compiled**.
It does not prove the block now holds the code you meant to send. Verified 2026-09-09: a push of a
67KB block came back clean and had silently dropped one blank line at a read-chunk boundary — valid
JavaScript, so the compiler had nothing to say. Only a byte comparison caught it. Treat every push as
unverified until the deployed source is proven identical to your file.

**Since 2026-10-01 that proof is a hash, not a download.** Push results (create, full replace,
search-replace) and `vibe_coding_block_get_code` carry `sourceSha256` and `sourceBytes`: the SHA-256
of the UTF-8 source Softr persisted, and its length in bytes. A failed compile stores nothing and
reports neither field. With `includeCode: false`, `vibe_coding_block_get_code` returns the digest and
`sourceCode: null`. Verified live 2026-10-01: a deployed block's `sourceSha256` equalled the SHA-256
of the exact source last pushed to it (taken from the push call), and the read came back at about
1 KB for a 15 KB block. The same check showed that block's local mirror had picked up three comment
edits since that push, which is exactly what step 1 below exists to catch. (The digest on push results is per Softr's release notes; no push of ours has shown it yet.)
Right after that release our client's copy of the tool definition did not declare `includeCode`, so
the argument went out as the string `"false"` and the server still honoured it. Whatever the loaded
definition says, check that `sourceCode` came back `null`.

**The protocol, per block:**

1. **Before editing, prove deployed == disk.** Call `vibe_coding_block_get_code` with
   `includeCode: false` and compare `sourceSha256` and `sourceBytes` to `shasum -a 256 <file>` and
   `wc -c < <file>`. If they differ, someone changed the block in Studio since your last push: fetch
   the full source, diff it against yours and reconcile. Do not overwrite work you have not seen.
2. Edit the local file. Run a parser and `no-undef` lint on it first — `node --check` does **not**
   accept a `.jsx` extension, so use esbuild (`esbuild file.jsx --loader:.jsx=jsx --jsx=automatic
   --log-level=error --outfile=/dev/null`) plus eslint with `@babel/eslint-parser`. The bugs that
   actually bite Softr blocks are semantic — `useRecordUpdate({ select: … })` instead of `fields:`,
   an invented identifier — and the push is the first thing that reports them.
3. Push the **entire** file — or, for a targeted patch on a large block, send search-replace ops
   and apply the identical ops to the mirror
   ([recipe above](#which-edit-tool-full-replace-vs-targeted-search-replace)).
4. **Compare the push result's `sourceSha256` with the hash of what you meant to deploy.**
   Identical, or you are not done: diff, fix, re-push. If the result carries no digest (an older
   server instance can answer during a rollout), read it with `includeCode: false`. If that has none
   either, fall back to fetching `sourceCode` and comparing byte for byte. Most clients save a large
   result to a file rather than returning it inline, so compare from that file with a script, never
   by eye.

Matching hashes prove what Softr stored, not how the block behaves: for that, check it in a fresh preview with saves blocked, per [browser-checks.md](browser-checks.md).

**Hash the exact bytes, trailing newline included.** Softr stores exactly what it receives: across
112 push→fetch pairs between 2026-09-09 and 2026-09-30 the fetched
`sourceCode` was byte- and MD5-identical to the text sent, including two pushes sent *without* a
final newline and stored without one. The "deployed block is one byte shorter" we chased on
2026-09-09 was our own read: an agent that reads a large file in chunks can drop the final
newline (or a blank line at a chunk boundary) before transmission. A comparison that normalises
the trailing newline hides exactly that class of error — so do not normalise anything; a mismatch
means re-send, whatever the byte.

**One file, two blocks, two datasource pairs.** When the same source is deployed to two pages, the
local file holds ONE page's `datasource.define()` pair. Push it as-is to that block; for the other,
build the swapped text in a scratch location, push that, and verify each block against the hash of
its own expected text (disk for the first, disk-with-swap for the second). Never save the swapped copy over
the local mirror — the mirror records which page it belongs to, and the block's header comment
records the other page's pair. Search-replace would avoid the swap altogether
([above](#which-edit-tool-full-replace-vs-targeted-search-replace)) — when the client can send its
array argument ([below](#the-array-argument-rejection-and-why-it-is-a-security-issue)).

**Do not read a 100KB block into a model's context to push it.** The full-replace tool takes the
whole file as a string parameter, so the source has to pass through whatever is making the call.
Verification no longer has to: the digest is a few hundred bytes. A large multi-block deploy is still
safer farmed out one file per subagent — a fresh context per file means no compaction can land
mid-file — and the hash comparison is what makes that delegation safe, not trust in the agent. The
steps that need judgement are the *edit* and the *review of the diff*; the hashing, the compare and
the push itself are mechanical, and can run on the cheapest tier available without lowering the bar,
because a wrong result fails loudly rather than plausibly.

**What a push also resets.** Every code push puts the block's derived Actions back on Softr's
default permissions (see the next section for why that can be a security problem and how to verify
the restoration). If page-level visibility is the access control in your app, record that decision
so nobody chases the reset after every round; if it is not, re-tighten and read back.

### The array-argument rejection, and why it is a security issue

**Several workspace-server tools take an array argument, and a call that sends it as a JSON *string*
is rejected** before it reaches any business logic. Since 2026-10-01 the error names the parameter
(wording from Softr's release notes):

```
Parameter 'updates' must be an array of objects, but a string was sent. It looks like JSON
encoded as a string — send the value itself, not a string containing it.
```

Before that, the same rejection came back as a bare Jackson message:

```
Cannot deserialize value of type `java.util.ArrayList<java.util.Map<String,Object>>`
from String value (token `JsonToken.VALUE_STRING`)
```

| Tool | Array argument | First fix | Fallback if it still fails |
|---|---|---|---|
| `vibe_coding_block_update_code_search_replace` | `operations` | Start a fresh session (below) | Use `vibe_coding_block_update_code` (full replace) |
| `vibe_coding_block_set_action_visibility` | `updates` | Start a fresh session (below) | **NONE — a human must fix it in Studio** |

**Where the string comes from: tool stubs on the client side (found 2026-10-01).** In the sessions
we examined, our client (Claude Code) at times held the Softr tools as **stubs**: the description is
just the tool name and the input schema is `{"type":"object"}`, with no properties. A stub declares
no types, so an array argument goes out as a JSON string and Softr rejects it. Nothing is written,
so the failure is safe, but no amount of care on the caller's side gets an array through a stub.
The evidence, from the complete transcripts of one build:

- On 2026-09-09 every successful array call came before that session was resumed, and every
  rejected one came after.
- On 2026-09-30, after the session was picked up again, every Softr tool definition the client
  recorded was a stub: in the session itself and in all 47 subagents it spawned. A live tool-list
  update from the server that day did not change that.
- Only two things ever replaced the stubs with real definitions: re-adding the connector (once) and
  a fresh session (2026-10-01).
- Not every pick-up produced stubs: a session picked up on the morning of 2026-09-09 held real
  definitions. So the trigger is not fully understood. The stubs most likely come from our side
  rather than Softr's server, since a fresh session got full definitions from the same server.

This replaces two earlier explanations in this file: that the model "had not loaded the tool
definitions" (2026-09-10), and that the workspace server's tools "can arrive schema-less"
(2026-09-30). Both were describing the stubs without knowing where they came from. The old remark
that Softr's *per-application* servers advertise empty schemas is withdrawn too. Every per-app
definition we ever recorded had the same stub signature, and Softr reports that those servers
publish full schemas.

**The rule:** before any array-argument call, look at the tool's loaded definition (ToolSearch shows
it). If the description is just the tool name and there are no `properties`, do not make the call:
start a fresh top-level session first. A subagent is not a fresh session; it inherits the stubs.
That matters most for `vibe_coding_block_set_action_visibility`, which
has no fallback. For a code edit, a full replace is an acceptable stopgap: one file per subagent for
a large block, hash-verified.

**Why the second row is a security problem, not an inconvenience.** Every code push rebuilds the
block's auto-registered Actions at Softr's default permissions. Per Softr (2026-10-01), the default
for **ADD_RECORD follows the block's own visibility**. On a block everyone can see, it comes back
`ALL_USERS`, writable by logged-OUT visitors. UPDATE_RECORD and DELETE_RECORD are always reset to
`LOGGED_IN_USERS`. That is what we saw on 2026-09-09, when one round of pushes (two saves, one per
block) left four ADD_RECORD actions open across two blocks and every restore call was rejected. The remedy is to re-apply the permissions with
`vibe_coding_block_set_action_visibility`. When that call is the one that fails, a routine cosmetic
push silently leaves public write access on the block. Nothing in the push result says so: the push
itself returns `errors: null, warnings: null`.

This is the platform's behaviour, not an MCP quirk. Per Softr, Studio rebuilds the Actions the same
way: on a Save in the code editor, an AI-assistant edit, a search-replace or a version restore. Only
`OPEN_CHAT` and `TRIGGER_CUSTOM_WORKFLOW` actions survive a recompile intact. As of 2026-10-01 nothing
preserves explicitly set permissions across a recompile, so every recompile needs the restore below.

**So treat permission restoration as a step that must be VERIFIED, never assumed:**

1. **Before the push, record what was set.** `vibe_coding_block_get_settings` lists each action
   with its `actionType`, `dataSourceId`, `permission` and `isDefaultVisibility`. Every action with
   `isDefaultVisibility: false` was set by someone, and the push will discard it.
2. Push the code.
3. **Re-apply** with `vibe_coding_block_set_action_visibility`. Address each action by `actionType`,
   plus `dataSourceId` when the block has several actions of that type. Never address one by its
   action id, because every compile issues new ids. Each update **replaces** that action's whole
   permission (`predefinedGroup`, plus `customGroups` and `recordCondition` where used), so send the
   complete intended state, not a delta. These rules come from the tool's own description
   (2026-10-01).
4. **Read the permissions back with `vibe_coding_block_get_settings` and confirm each one actually
   changed.** A successful-looking sequence is not evidence; the failure is an argument rejection, so
   the call errors rather than lying, but an agent that batches calls can easily miss which one failed.
5. If any action is still broader than intended (typically ADD_RECORD at `ALL_USERS`), **report it
   and let the builder decide.** Check the page's own VIEW permission first with
   `application_page_get_permissions`, because that is what sets the severity, and report the
   block's own Visibility with it (`vibe_coding_block_get_settings`): it gates the block's reads
   and sets ADD_RECORD's default (2026-10-05), but whether it refuses writes on its own is untested
   ([below](#what-the-server-enforces-on-a-blocks-data-endpoints)):
   - **Page VIEW is gated** (e.g. `LOGGED_IN_USERS`) — an anonymous visitor cannot load the page at
     all, so exploiting the open action means calling its endpoint directly, and the realistic worst
     case is junk records rather than data exposure or deletion. Housekeeping: worth fixing on the
     next Studio pass, not worth holding a release for.
   - **Page VIEW is `ALL_USERS`** — the action permission is the only gate known to hold on writes
     (the block's Visibility may also refuse them; untested). That is a genuine hole and deserves
     to be called one.

   Report page, block, action type, data source and current group; say which of the two cases applies;
   note that a human sets them on the block's Actions tab in Studio. Then stop — **do not unilaterally
   block the publish.** It is not your app, and the person whose app it is needs the finding and the
   severity, not a veto.

   One caveat worth stating: page visibility and action permissions are *separate* gates. Page VIEW
   **is** enforced on the block's datasource **records** endpoint (verified live 2026-09-18 — a
   viewer who cannot view the page gets a 403 whose message names "block/action visibility rules";
   see [below](#what-the-server-enforces-on-a-blocks-data-endpoints)). The *action* (write) endpoint
   refuses outsiders too: on 2026-10-05 a replayed PATCH from outside the block's group got 403
   ([hubspot.md](../datasources/hubspot.md#writing)). The block and its actions were both limited to
   that group, so which rule refused it is not known, and whether page VIEW alone gates writes is
   untested. So the reason to treat a gated page as low-severity is still the practical
   difficulty and low blast radius — and note that "gated to logged-in users" keeps out anonymous
   visitors only: any logged-in user can view that page, and therefore reach its endpoints. Say that
   plainly rather than implying the action is safe.

   **Calibration matters.** This guidance read "do not publish" in v2.5.1 and immediately fired at
   maximum severity on a logged-in-gated app where the real exposure was junk records. A warning that
   cannot distinguish housekeeping from a breach gets tuned out, and then it is worth nothing on the
   day it matters.

Do not improvise around a rejection. `vibe_coding_block_update_settings` is not a substitute: it writes
far more than one permission, and guessing its payload risks clobbering the block's data source
connections. Restoring an older block version is not a substitute either. It reverts the code you just
pushed, and per Softr a restore recompiles like any other save, so its Actions come back at the
defaults anyway.

Both edit paths recompile, so both reset Action permissions either way (Hard Constraint 21).

### What the server enforces on a block's data endpoints

*Verified live 2026-09-18 (Softr Database; draft preview, "Preview as" different users, requests
captured from the app iframe); the block-visibility row verified 2026-10-05 (HubSpot; preview link,
impersonated users, direct POSTs).* A block's data lives behind per-connection endpoints —
`/blocks/<blockId>/datasources/<connection>/records` for lists, `/records/<id>` for one record —
and these are the gates that actually exist on them (`<connection>` was recorded as the connection's id in the 2026-09-18 Softr Database capture and seen as its alias in a 2026-10-05 HubSpot capture; unresolved, and it only matters when reading a network log):

| Gate | Enforced server-side? |
|---|---|
| **Page VIEW permission** | **Yes.** A viewer who cannot view the page gets **403** ("block/action visibility rules…") from the block's datasource endpoint — crafting the request by hand does not get around it |
| **The block's Visibility** (`predefinedUserGroup` + `customUserGroupIds`; `vibe_coding_block_set_visibility`) | **Yes.** A viewer outside the block's group gets the same **403**, on list and by-id, even where the page lets them in. The body reads like a write error on a read: "You cannot add or edit a record because either the block/action visibility rules, user group conditions, or the user/record data in the datasource has changed." Per block: the same table on an ungated block stays open. Five code pushes left the setting intact |
| **The connection's Source conditions** (Source tab / `vibe_coding_block_set_data_source_record_filters`) | **Yes — and they are the only server-side ROW gate.** A by-id request for a record the condition excludes answers differently per backend: **HTTP 200 with an empty body** on Softr Database (2026-09-18), **404** on HubSpot (2026-10-05). Treat both as "not found" |
| A `where` filter in the block's code | No — it is a request parameter the caller controls |
| Which fields the block *renders*, a second / conditional `q.select`, `enabled: false` on `useRecords` | No — the endpoint returns the union of the connection's read selects to anyone allowed to call it (see [multi-datasource.md](../datasources/multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects)) |

The consequence to design around: **on a page any logged-in user may view, every datasource
connected to its ungated blocks is readable by any logged-in user who crafts the request** — all rows the
Source conditions allow, all fields the block's read selects name. A per-record access check in
React ("is this viewer a party to this record?") shapes the UI; it is not access control. When rows
must be private per user, put it in the Source conditions (e.g. a logged-in-user condition; see
[below](#logged-in-user-values-in-source-conditions) for the two forms known to work) or on a
page only the right group can view. When a field must be private, a second connection of the table
keeps it out of every ordinary browser's payload — but not away from a crafted request by someone
who may view the page; for that it has to live on a page (or in a group-gated block) the viewer
cannot see. Conversely, a block gated to a staff group may read unfiltered connections for a staff
view: on 2026-10-05 group members got all 41 deals and 16 tickets, and everyone else got 403, with
the page VIEW permission at `LOGGED_IN_USERS` throughout.

This is also what makes the open-`ADD_RECORD` finding above severity-dependent on the page's VIEW
permission rather than uniformly critical.

#### Logged-in-user values in Source conditions

*The email token was verified on Softr Database in a production project: set in Studio's Source
tab and read back with `vibe_coding_block_get_settings` on 2026-09-01, then set over MCP and checked
against the records endpoint's totals as different users on 2026-09-18. The user-field token was
verified on HubSpot on 2026-10-05, the same way.* There are two forms, and **their braces differ**:

- **The email: `{USER:::EMAIL}`, with braces, only as the ENTIRE value** of an expression, e.g.
  `{ "subject": { "field": "<fieldId>", "type": "TEXT" }, "operator": "CONTAINS", "value": ["{USER:::EMAIL}"] }`.
  Softr substitutes it as a whole-value token, not by string interpolation. The embedded form
  `",{USER:::EMAIL},"` returned total 0 for every user, including users who should have matched.
- **A users-table field: `USER:::<user field id>`, with NO braces, as the entire value** (verified
  2026-10-05 on HubSpot). `associations.company IS_ONE_OF ["USER:::associations.company"]` on a
  deals connection gave each user only their own companies' deals. Studio stores a picked user
  field in this form (Leo set it in the Source tab, and it read back that way), and the same form
  works when written with `vibe_coding_block_set_data_source_record_filters`.
  **It fails closed:** a user whose field is empty, or who has no record in the users' data source,
  gets 0 rows, and a by-id request for a record outside the condition returns 404 (on HubSpot;
  Softr Database answers HTTP 200 with an empty body).
- **Use AND between rules.** With one rule OR and AND behave the same, but a second rule added
  under OR widens access (2026-10-05).
- **The braced user-field spellings fail.** On 2026-09-18, on Softr Database, eleven spellings were
  tried, including `{USER:::<fieldId>}`, `{USER:<fieldId>}` and `{USER:::FIELD:<fieldId>}`. Each
  silently matched nothing. All eleven had braces, so the braceless form is untested on Softr
  Database, not disproved. A subject of `USER:<fieldId>`, the syntax user-group rules use, returned
  HTTP 400 "Field not found": the user field goes in the value, never the subject. No token for a
  user group has been found.
- Studio's conditional-filter UI offers the logged-in user's Email and Email-Domain, plus every
  users-table field once users sync from a data source (documented). For a value not listed here,
  pick it in a block's Source tab, save, and read `dataSources[].condition` back with
  `vibe_coding_block_get_settings`. That is how the user-field form was found.
- **CONTAINS against a list of emails has a substring trap:** `bob@x.com` matches a field holding
  `jbob@x.com`. Prefer IS against a single-email field. If a record must hold several emails, the
  delimiter trick the embedded form was meant to provide does not work, so accept the trap or
  split the data.
- When a row gate must follow something other than the user's email (a company, a team), compare
  the record's field with the user's own field through `USER:::<user field id>`. Where that form is
  untested (Softr Database so far), store an email on the record and compare it with
  `{USER:::EMAIL}`. Staff who need every row get a group-gated block with unfiltered connections
  ([above](#what-the-server-enforces-on-a-blocks-data-endpoints)), not a wider condition.

For HubSpot specifics (association-based scoping, owner fields), see
[../datasources/hubspot.md](../datasources/hubspot.md#row-scoping--who-sees-which-records).

## Adopting Studio-AI-generated code

When you pull a Studio-AI-generated block via `vibe_coding_block_get_code` to adopt into a project repo as source of truth: its output renders fine but ships with predictable defects. **Functional patterns in Studio output are platform-support evidence** (it surfaces undocumented capabilities before the docs do — see SKILL.md's "Platform truth sources"); **its code hygiene is not a pattern to imitate.** Cleanup pass before committing:

- **Run a formatter** — Studio output ships inconsistent indentation (observed: statements at column 0 inside a 4-space-indented component).
- **Hoist and consolidate brand hexes** into module-scope constants; flag near-duplicate hexes as probable unintended drift (observed: `#AE5E3D` vs `#B4603D` for one terracotta in a single block).
- **Fix React keys on settings-array loops** — Studio emits `key={item.label}`; use `key={index}` (see [anti-patterns.md](anti-patterns.md#editable-settings)).
- **Add the guards Studio omits** — conditional render for empty media settings, `whitespace-pre-line` on long-text settings, mobile nav for block-owned headers, `aria-hidden` on decorative glyphs.
- **Rewrite absolute self-domain URLs relative** (`https://<app>.softr.app/#x` → `/#x`) — observed as a configured setting value on a Studio-generated hero, 2026-08-31.

This is distinct from SKILL.md's no-churn rule: cleaning up a block you're ADOPTING into the repo is required; modernizing a deployed working block's syntax is still churn — don't do that.

## Vibe coding gotchas (official)

From the official MCP docs — these hold for MCP-driven and Studio-driven edits alike:

- **A broken block can't be saved.** Code is validated before storage; on failure the block keeps its last working state and nothing is lost.
- **A version is a snapshot of the whole block** — code, settings, visibility, AND data source connections. Setting-only changes don't create a version.
- **Rolling back reverts more than the code.** Restoring a version also restores settings, visibility, and data source connections as they were at that point. Action permissions are the exception: per Softr (2026-10-01) a restore recompiles, so the restored block's Actions come back at the default permissions, not as they were.
- **Changing the code resets action permissions.** Any code change rebuilds the block's record actions at default visibility — restrictions to user groups must be re-applied. (This is Hard Constraint 21 in SKILL.md, now officially documented: tighten Action permissions only after the LAST redeploy.) The defaults: ADD_RECORD follows the block's own visibility, while UPDATE_RECORD and DELETE_RECORD are reset to logged-in users (per Softr, 2026-10-01).
- **A block with an unconnected data source saves without complaint**, then errors when the page loads. If a freshly created block looks broken but the code seems right, check its data source connection first.

## Application management tools

The Applications area goes well beyond reads (roster as delivered 2026-10-01; behavior not individually exercised unless stated):

| Group | Tools |
|---|---|
| Apps | `application_list`, `application_get`, `application_create` (create a whole app via MCP), `application_set_name`, `application_set_subdomain`, `application_set_domain`, `application_set_login`, `application_configure_sign_up`, `application_configure_email_sender`, `application_update_data_source` (point/swap the app's data source), `application_update_pwa_settings` (installable-app name, short name and theme colour; new 2026-10-01) |
| App users and groups | `application_list_users`, `application_add_user`, `application_remove_user`, `application_set_user_activation`, `application_list_user_groups`, `application_create_user_group`, `application_update_user_group`, `application_delete_user_group`, `application_create_user_connection`, `application_get_user_connection`, `application_remove_user_connection` |
| Pages / blocks / permissions | `application_page_list`, `application_page_get`, `application_page_create`, `application_page_get_block`, `application_page_get_permissions`, `application_get_access_overview` (user groups plus counts of redirections and data restrictions) |
| Publish / preview | `application_preview`, `application_publish` |
| Workspace | `workspace_list`, `workspace_list_email_senders`, `get_workspace_integrations` (distinct from the [integrations drill-down](#browsing-integrations-external-data-sources) below) |

Combined with the database tools (`database_create` / `database_create_table` / `database_create_field`) and `vibe_coding_block_create` + `application_publish`, the tool set for scaffolding a full app end to end now exists. (Existence-verified only — that pipeline hasn't been run live; treat the first full scaffold as an experiment, not a routine.)

**Etiquette from the server's own instructions:** after changing a block, link the page as `https://studio.softr.io/applications/{applicationId}/pages/{pageId}`; offer `application_preview` or `application_publish`, but **only publish when the user asks**.

> **application_preview links are auth tokens.** Per the server's own instructions, a preview link **signs its opener in as the user who requested it** and lasts about a day. Give it only to that user, and mint a fresh one with another `application_preview` call rather than re-sending an old link. Never paste a preview link into a shared channel.
>
> **A preview link also pins the app version.** Its URL carries `&version=<n>`, so it keeps serving the version it was minted for. That is by design, not a caching bug. After every push, mint a new link before you check anything.

**Reading pages and blocks:**

- `application_page_get` lists a page's blocks **in page order, with no `order` field**. That field
  was always `null` and was removed on 2026-10-01 (verified live that day; the tool's description
  still mentions it). For a block nested in a column or tab container, the container's slots set its
  position, not its place in the list.
- **A block created over MCP still lands at the bottom of the page**, and no tool places or reorders
  blocks yet. Softr has said placement will come later. Until then, a human drags it into place in
  Studio. Say so when you hand the block over.
- **Timestamps are UTC with a `Z`.** Since 2026-10-01, timestamps such as `publishedAt` or a
  version's `createdAt` are ISO-8601 UTC with millisecond precision, studio-side and tables-side
  alike (per Softr; verified on `vibe_coding_block_list_versions` that day). Before then, studio-side timestamps came back with
  no zone designator and nine fractional digits (`2026-09-09T22:34:11.157881061`). They were UTC, so
  read any older logged value as UTC, never as local time.

### Testing as any app user without logins — the "Preview as" switcher

*Verified live 2026-09-18.* The `application_preview` link does not open the app directly: it opens a
**toolbar shell** with a **"Preview as" user switcher**, and runs the draft app in an **iframe**
whose URL carries `?autoUser=true`. That is a complete role-testing rig — every user group, no
passwords, no test accounts to create:

- The switcher is a **Choices.js** select listing the app's users. Picking one raises a
  confirmation modal ("Ok, I understand"); after confirming, the app runs as that user, and the
  choice persists per browser.
- **With the Browser pane visible**, click through it like a person would.
- **With the pane hidden, drive it by script** in the shell page: dispatch `mouseover` then
  `mousedown` on `.choices__item--choice[data-value="<email>"]` (Choices.js acts on
  `mousedown`, not `click`), then click
  `#userConfirmationModal button.submit-btn`.
- **To see what a block really sends and receives**, set `iframe.src` to the page under test and
  wrap `iframe.contentWindow.fetch` immediately afterwards, recording each request body and
  response. This is how the union-of-selects, `pageContext: null` and `enabled: false` findings in
  [../datasources/](../datasources/) were established — read the wire, not the rendered UI.
- Blocks render in shadow roots inside that iframe: read the DOM through
  `iframe.contentDocument` and each block host's `shadowRoot`, not `document.querySelector`.
- **Switch user without the switcher** (verified 2026-10-05): on the preview link's origin,
  `fetch('/studio/impersonate/<softrUserId>')` makes the preview run as that user. The id is the
  user's Softr id from `application_list_users`. It works from a fresh preview link, so it needs no
  Studio session in the browser.
- **Press the preview's own `#refresh-button` after a push.** An open preview kept serving the old
  block version until it was pressed (verified 2026-10-05). Minting a fresh link does too (see the
  version note above).

> **The preview is wired to the LIVE datasource.** Anything clicked there — a Save, a status
> change, a form submit — writes real records, as the previewed user. Keep preview sessions to
> read-only checks unless the record is a marked test record, and never run a write path "just to
> see" against client data.

Limits: a page gated to a user group nobody belongs to cannot be previewed until someone is in the
group, and these selectors are Softr's shell internals — observed, not documented, so re-inspect
the shell if a selector stops matching rather than assuming the feature is gone.

## Browsing integrations (external data sources)

An integration is anything connected once per workspace. **A data source is one kind of integration**: one that holds records, such as Softr's own databases (`SOFTR_TABLES`), Airtable, Google Sheets, Notion or a SQL database. A proxy-only integration (Gmail, Slack, OpenAI, …) has no records and nothing to browse. Each entry from `integration_list` carries `capabilities` (`DATA`, `PROXY`, or both) that says which kind it is, so read that rather than guessing from the type. Five read-only tools drill down from workspace to fields; each level needs an ID from the level above:

```
integration_list                     the workspace's integrations: id, name, type, capabilities
└── integration_list_databases       the top level of one data source: an Airtable base, a spreadsheet,
    │                                an Excel workbook, a Notion database, a Coda doc, a SQL database, …
    └── integration_list_schemas     only for SUPABASE, POSTGRESQL, SQL_SERVER, SNOWFLAKE (a SQL schema),
        │                            GOOGLE_BIGQUERY (a dataset), SMARTSUITE (a solution), CLICKUP (a space)
        └── integration_list_tables          tables or sheets
            └── integration_list_table_fields   fields, types, options, primary field
```

**Which types can be browsed and connected through MCP.** Per the tools' own descriptions
(2026-10-01): `SOFTR_TABLES`, `AIRTABLE`, `GOOGLE_SHEET`, `MICROSOFT_EXCEL`, `NOTION`, `MONDAY`,
`SMARTSUITE`, `CLICKUP`, `CODA`, `HUBSPOT`, `SALESFORCE`, `ZOHO_CRM`, `REST_API`, `GOOGLE_BIGQUERY`, and
the SQL vendors `SUPABASE`, `POSTGRESQL`, `MYSQL`, `MARIADB`, `SQL_SERVER`, `SNOWFLAKE` and `XANO_SQL`.
Anything else `integration_list` returns is proxy-only. This replaces the five types (Softr Databases,
Airtable, Google Sheets, Notion, Supabase) this file listed on 2026-08-31. Only the Softr Databases path
has been exercised end to end by us. For the flat sources (HubSpot, Salesforce, Zoho CRM, REST API)
the "database" and the "table" are the same object, so `integration_list_tables` echoes back what you
picked. For Softr's own databases these tools only resolve IDs for
`vibe_coding_block_connect_data_source`; for records, fields and aggregates use the
[database tools](#softr-database-tools).

**How fields must be referenced in `q.select()`.** Once a source is wired to a block, the
authoritative answer is that block's own `dataSources[].fieldReferenceKey` (`id` or `name`) in
`vibe_coding_block_get_code`. Before that, `integration_list_table_fields` tells you, and this is what
we verified earlier:

| Integration | Reference fields by |
|---|---|
| Airtable, Google Sheets, Notion | Name |
| Softr Databases, Supabase | ID (for Supabase, the SQL column name) |

For the types added since, read `fieldReferenceKey` rather than guessing. Getting this wrong **fails silently** — the code compiles, saves, and looks right in the builder, then returns nothing at page load. If a block renders but its data is empty, check this first.

## Softr Database tools

For Softr's native databases the MCP goes far beyond browsing: `database_get_field_reference` (authoritative field-type + filter-operator reference — call it before creating/updating tables, fields, or filters; the server's own instructions say "do not guess field types, options, or operators"), database/table/field CRUD **including deletes** (`database_delete`, `database_delete_table`, `database_delete_field`), `database_list_views`, record reads (`database_list_records`, `database_search_records`, `database_get_record`), record writes (`database_create_record`, `database_create_records` batch, `database_update_record`, `database_delete_record`, `database_delete_records` batch), `database_aggregate_records` for grouped summaries, and `database_search` to find a database by name when the account has many.

**Call economy (from the server's own instructions):** `database_get_table` returns a table's metadata AND all its field definitions in one call; `database_list_fields` returns the fields alone. Call ONE of them once per table and reuse the result — never both — and re-fetch only after you changed the table's fields yourself.

**`database_get_field_reference` (was `get_schema`).** It describes the whole product, not one table: it takes no table ID and returns the same content every time. Live-confirmed 2026-08-31 (and in reads of 2026-08-26 and 2026-09-09): `readOnlyFieldTypes` = AUTONUMBER, COUNT, CREATED_AT, CREATED_BY, FORMULA, LOOKUP, RECORD_ID, ROLLUP, UPDATED_AT, UPDATED_BY. On 2026-10-01 the list was the same without COUNT, which no longer appears in either the read-only list or the field types. The `LINKED_RECORD` value example is `["record-id-1", "record-id-2"]` — independently corroborating the verified string-array write shape in [../datasources/softr-database.md](../datasources/softr-database.md). On 2026-10-01 it listed `allowMultipleEntries` among the available options of SELECT and LINKED_RECORD. Operator families include relative-date `IS_WITHIN` / `IS_NOT_WITHIN` ("last 7 days"), ternary `IS_BETWEEN` / `IS_NOT_BETWEEN`, and `AND`/`OR` composites. **Schema-drift caution:** this reference and the [per-application servers'](#per-application-mcp-servers) `get_schema` have drifted. The per-app catalog lists creatable types the workspace one omits: ADDRESS, PROGRESS, TIME, DATE_RANGE and BUTTON were still absent from the workspace reference on 2026-10-01, although, per Softr, the workspace server returns fields of those types. The operator NAMES differed too (workspace `GREATER_THAN` / `DOES_NOT_CONTAIN` vs per-app `GT` / `DOES_NOT_CONTAINS`, observed 2026-08-31); per Softr the per-app names were realigned on 2026-09-09, which we have not re-checked. Do not assume a filter payload is portable between the two kinds: call the reference of the server you are actually using.

Known limits and behaviors (per official docs):

- Record field keys are **field IDs**, not labels — `database_list_fields` maps between them.
- Computed fields (formula, lookup, rollup, count) and system fields (created/updated time and by, autonumber, record ID) are read-only; a field's type cannot be changed after creation.
- **Deletion now exists** (supersedes the earlier "nothing can be deleted through the MCP yet" finding): `database_delete_record`, `database_delete_records` (batch), `database_delete_field`, `database_delete_table`, and `database_delete` are all in the roster (verified 2026-08-31 under their old names), and per-app servers add `delete_record` + `batch_delete_records`. Roster-verified only — no destructive call was made, so which Databases permission level gates them and how cascades behave (e.g. deleting a table with linked records) are untested. Treat every delete as irreversible; no soft-delete is documented.
- **Attachment writes take a URL and copy the file.** `database_create_record` / `database_update_record` accept
  `{ filename, url }` on an ATTACHMENT field with any publicly reachable URL; Softr fetches it, stores its
  own copy and generates thumbnails, so backfilling images from another system is one write per record
  with no upload step. Verified 2026-08-26 — see [../datasources/writing.md](../datasources/writing.md#attachment).
- **Before 2026-10-01, every `update_field` call damaged the field it touched.** Per Softr, the
  handler ignored the `options` it was sent and wrote `allowMultipleEntries: false` on every call, so
  a multi-select became a single-select and a multi-link a single-link. It also cleared the field's
  default value, and blanked its description whenever none was sent. This file used to say the tool
  "silently ignores `allowMultipleEntries`" (2026-08-26) and "silently drops added SELECT choices"
  (2026-09-01); both were the visible half of that. If the old tool was ever run against a table you
  care about, read those fields back and check them.
- **Since 2026-10-01, `database_update_field` applies `options` on top of the current field** (per
  Softr; not yet re-tested by us). Each key you pass replaces that key's stored value. Keys you leave
  out are kept, `allowMultipleEntries` and the default value included. Unknown keys are rejected,
  `allowMultipleEntries` now goes **inside `options`**, and an omitted description is left alone. A key
  you pass still replaces its whole value: sending `choices` replaces the choice list, and the tool's
  own description warns that narrowing it can orphan choices already held in records.
- **The proven way to add a SELECT choice is the Tables API, with a full body** (verified
  2026-09-09): `PUT /api/v1/databases/{db}/tables/{t}/fields/{f}` with
  `{ name, type, options: { choices: [...], allowToAddNewChoice } }`, every existing choice carrying
  its own `id` and the new one none (the server assigns it). A partial body returned 400 then. The
  array order is kept, so a new choice can be slotted where it belongs rather than appended. Two other
  routes: add it in Studio, or, when the field has `allowToAddNewChoice` enabled, the first record write
  with an unknown label creates the choice.
- **Flipping a LINKED_RECORD between single and multi through the Tables API** (verified
  2026-08-26): `PUT` the field with `allowMultipleEntries` at top level, and always echo
  `options.inverseLinkFieldId` in that PUT, because omitting it severs the inverse pairing. Full
  write-up, including the silent on-write clobbering of single-valued link pairs and the truthy-`[]`
  empty-link read shape:
  [../datasources/writing.md](../datasources/writing.md#linked-record-write-traps-verified-live-2026-08-26).
  Read any field back after changing it, whichever route you used.
- **`database_update_table` sends only what you pass, since 2026-10-01.** Before then, per Softr,
  `update_table` wrote an empty value over whichever of name and description it was not given, so a
  plain rename blanked the description. Now a blank name is ignored and a blank description clears it.
  A table's `updatedAt` also advances on every write now. It never did before, so an older `updatedAt`
  is no evidence that nothing changed.
- **Field descriptions are readable** since 2026-10-01 (per Softr). Before then a description
  could be written but no read returned it.
- Limits: 100 records per `database_create_records` call, 200 records per read (silently capped, not an error), 2 group-by fields in `database_aggregate_records`. For big tables prefer a filter or aggregate over paging.

Typical Vibe Coding uses: "list every field on `Wigs` with id, name, type, and dropdown options", "what's the option id for `Payment status` = 'Partially paid'?", "show 3 sample records so we know value shapes", "verify the field id in my `q.select()` exists". This eliminates the field-id-typo / wrong-option-uuid class of bugs entirely.

## Workflows

Softr Workflows are automations built from trigger + action nodes, and the MCP can build, wire, test, and publish them — a **28-tool suite** (26 roster-verified 2026-08-31, plus `test_workflow` and `update_node_retry` in the 2026-10-01 roster; these tools kept their names in the 2026-10-01 rename; the full build → wire → test → publish loop **exercised end to end 2026-09-01** — 10 production workflows built live through MCP; see the build-loop findings below):

| Group | Tools |
|---|---|
| Workflow lifecycle | `workflow_create`, `workflow_get`, `workflow_get_url`, `workflow_list`, `workflow_rename`, `workflow_update_configuration`, `workflow_publish`, `workflow_unpublish`, `workflow_test` |
| Node management | `workflow_add_node`, `workflow_add_branch_node`, `workflow_create_branch`, `workflow_delete_node`, `workflow_duplicate_node`, `workflow_rename_node`, `workflow_reorder_node`, `workflow_reorder_multiple_nodes`, `workflow_replace_node`, `workflow_replace_trigger_node`, `workflow_update_node_inputs`, `workflow_update_node_note`, `workflow_update_node_continue_on_error`, `workflow_update_node_retry` |
| Discovery / testing | `workflow_list_node_types`, `workflow_get_node_specifications`, `workflow_get_dynamic_input_options`, `workflow_test_node`, `workflow_get_node_output` |

These are the current names (live roster, 2026-10-06). Until 2026-10-01 they had no `workflow_`
prefix (`create_workflow` → `workflow_create`), and older notes, including project docs, still use
those; see [the rename note](#tool-names--the-2026-10-01-rename).

**The node catalog is huge** — live-enumerated 2026-08-31: **418 node types (58 triggers + 360 actions) across 56 applications.** The parts that matter most for this skill:

- **Softr-native triggers:** one-time + recurring schedules, `WEBHOOK` (inbound webhook), `SOFTR_EMAIL_RECEIVED` (inbound email! — delivery mechanism not captured), Softr Databases record events (added / updated / deleted / meets-conditions / enters-view / "run custom workflow on selected records"), Softr Apps events (Add Record form submitted, Edit Record form submitted, form submitted, user added, comment added) — and **"Run custom workflow"** (`SOFTR_APPS_TRIGGER_WORKFLOW`; this file called it "Run Custom Workflow action triggered" until 2026-10-05, and the live label is "Run custom workflow"). This is the receiving end of the vibe block's `TRIGGER_CUSTOM_WORKFLOW` action.
  - **From the block:** the live developer guide documents `navigate(setting, { recordId, datasourceId })` on a `TRIGGER_CUSTOM_WORKFLOW` setting, callable for example from `useRecordCreate`'s `onSuccess`, and says "the builder picks which action it points at" (documented, checked 2026-10-05). We have not yet run it end to end ourselves.
  - **The trigger and its payload:** its only input is `corsAllowedOrigins`. Saved payloads look like `{ body: { ... }, query: {} }`, with `body` holding whatever the triggering action mapped. Native buttons can map form or record fields; the vibe path documents only `recordId` and `datasourceId`.
  - **Who can call it:** the endpoint is browser-callable (per its spec, an empty `corsAllowedOrigins` allows any origin), so re-read the record server-side rather than trusting the body.
  - **Wait screen:** `workflow_create` scaffolds the Show Wait Screen and End User Interactions steps for this trigger. Whether a vibe `navigate()` call shows the wait screen is undocumented; the docs describe the toggle only on native app actions.

  See SKILL.md's NavigationAction action-types list.
- **Softr-native actions:** `BRANCH`, `FILTER`, `WAIT`, `LOOP_ACTION_GROUP` (run each list item through the same steps), `SOFTR_SEND_EMAIL`, `CALL_API` (REST), `WEBPAGE_SCRAPPER`, `PDF_TO_TEXT`, `COMPRESS_FILES` (zip + download link), `TRANSFORM_DATA`, `RESPONDED_TO_WEBHOOK` (custom HTTP response to the webhook caller); Softr DB record CRUD incl. bulk update/delete and find; Softr Apps user management (find / create / delete / deactivate / activate / invite user, send push notification).
- **`CUSTOM_CODE`:** runs custom **JavaScript or Python** inside a workflow.
- **AI actions:** Softr AI, OpenAI, Anthropic, Gemini, and Mistral each ship Write / Summarize / Categorize / Custom-prompt nodes; OpenAI adds gpt-image-2 image generation. Pinecone, Firecrawl, Replicate, and Linkup nodes exist too.
- **Integration apps (top of 56):** Stripe (36 nodes), QuickBooks (24), ActiveCampaign (23), SharePoint (22), Asana (18), Gmail/Attio/Brevo/Resend (12 each), ClickUp/Zendesk (10), Airtable/Notion/Cal.com/HubSpot/Xero/DocuSign/Apollo (9 each), Sheets/Excel (8), monday/SQL/Jira (7), Slack/Telegram (6), plus Salesforce, Coda, Calendly, Twilio, Zoom, Linear, Trello, form tools (Typeform/Tally/Jotform/Fillout), and more.

**Mechanics from the server's own instructions:**

- Node inputs can embed **references to another node's runtime output**, a loop's current item, or named date/time tokens.
- **Test-first is mandated:** every testable node needs a test run before its outputs become referenceable by downstream nodes. Each node carries a `testRunMode` — `REAL_ONLY`, `MOCK_ONLY`, or `MOCK_AND_REAL` — so some nodes can only be tested against real side effects while others mock. See the test-safety rules under build-loop findings below before testing anything against a production workspace.
- **Workflows are owned by a workspace, and can now be pinned to an app** (verified 2026-10-05 from the tool definitions). `workflow_create` still requires a `workspaceId`; its optional `applicationId` "pins the workflow to it, so it is listed on that app's Workflows tab", and `workflow_list({ applicationId })` lists the workflows pinned to an app. Leave `applicationId` out for a workflow that belongs to the workspace as a whole. Pinning or not, `application_preview` / `application_publish` do not apply to workflows. Link a workflow as `https://studio.softr.io/workflow/{workflowId}`.

**Build-loop findings (verified live 2026-09-01, first end-to-end production build — 10 workflows):**

- **`workflow_create` instantiates an OLD version of the trigger node.** Immediately call `workflow_replace_trigger_node` with the **same trigger type** — the replacement lands at the current version with the current inputs. Example: `updateField` on `SOFTR_TABLES_RECORD_UPDATED` (fire only when a specific field changed) only exists at v1.2.0; the version `workflow_create` instantiates doesn't have it.
- **A FILTER condition written over MCP is inert — set it in Studio** (corrected 2026-10-06; this bullet used to say the MCP writes it). `workflow_update_node_inputs` with inputName `"condition"` accepts an `{operator, conditions: [...]}` object and stores it in the node's `inputs.condition`, a field the engine does not read. The engine evaluates the condition on the FILTER node's **outgoing path** (the `paths` entry whose `fromActionId` is the filter), and only the Studio builder writes that. **A filter built over MCP passes every run.** A 2026-09-19 audit of this very build showed it three ways: the one workflow actually running had empty `inputs` and its whole condition on the path; two others, edited in Studio afterwards, held one condition in `inputs.condition` and a different one on the path, so Studio reads and writes only the path.
  - **The official MCP docs agree:** "Branch and filter conditions can't be set through MCP yet ... deciding what sends a run down each path is something you finish in the builder" (docs.softr.io/mcp/workflows, checked 2026-10-05), and the FILTER spec declares `inputs: {}`. BRANCH conditions were not tested separately here; treat them the same way.
  - **How to build one:** add the FILTER over MCP if that is convenient, then open it in Studio, set its clauses and save. Never trust `inputs.condition` as a record of what the filter does; it can disagree with the path.
  - **How to check one:** read the workflow back with `workflow_get` and find the `paths` entry whose `fromActionId` is the filter; the condition must be there. FILTER nodes cannot be run with `workflow_test_node`, so this read-back is the only check before a real run.
- **`LOOP_ACTION_GROUP`'s `loopVariables.items` must reference a plain array**, e.g. `$.records` — a `[*]` projection (e.g. `$.records[*].fields.X`) is rejected by the validator. Per-item references **inside** the loop use `{loopActionGroup.<id>:::loopVariables.items.fields.<fieldId>}` (use the bracket form for ids that start with a digit).
- **`workflow_update_node_inputs` batches validate against the STORED node state**, not the batch-in-progress — an update that depends on another update in the same batch fails validation. Split dependent updates into sequential calls.
- **Test-safety rules** (which `testRunMode` means what in practice):
  - Record-**write** nodes (`SOFTR_TABLES_UPDATE_RECORD` etc.) are `REAL_ONLY` — **never test them against a production workspace**; the test performs the real write.
  - `SOFTR_SEND_EMAIL` is `MOCK_AND_REAL` — **always pass `mode: "mock"`**.
  - Triggers and `GET_RECORDS` are `REAL_ONLY` but read-only-safe; a record-updated / enters-view trigger test just samples an existing record.

**Why this matters to block work:** Softr Workflows are now the Softr-native answer to the "block writes to its own table, backend cascades the rest" pattern — for **Softr Database backends** what [airtable-automations.md](airtable-automations.md) is for Airtable backends. See the cross-table alternatives in [../datasources/writing.md](../datasources/writing.md#cross-table-operations).

## Per-application MCP servers

A separate product class from the workspace server (live-observed 2026-08-31 on two connected app servers): **one MCP server per published Softr app**, exposing that app's data to MCP clients. How these servers are provisioned/connected was not captured — check the app's settings in Studio or the official docs when setting one up.

**Tools (12):** `list_tables`, `describe_table`, `get_schema`, `get_records`, `get_record`, `get_linked_records`, `get_current_user`, `create_record`, `update_record`, `delete_record`, `batch_update_records`, `batch_delete_records`. These are this server's own names, last enumerated by us in late August 2026; the 2026-10-01 rename of the workspace server did not touch them.

**If the tool definitions arrive empty, do not conclude the server sent them that way.** Every definition of these tools our client ever recorded had a name-only description and an `{"type":"object"}` schema, the same signature as the stubs described [above](#the-array-argument-rejection-and-why-it-is-a-security-issue). Unlike the workspace stubs, these were stubs even at times when the same client held real workspace definitions, so their cause is not settled. Per Softr, these servers publish full schemas and descriptions. A tool with no arguments (`list_tables`, `get_schema`, `get_current_user`) works either way; before relying on one that takes arguments, start a fresh top-level session and check the loaded definition again.

**Live-observed semantics:**

- **The table catalog is derived from the app itself.** `list_tables` returns only tables a block on one of the app's pages is bound to, so an empty list means nothing is bound yet, not that the app has no data. Each entry's `tableId` and `tableName` came back as the same long `key=value` resource string (reported to Softr in September 2026; not among its 2026-10-01 fixes). Every table it does return comes with an `operations` array (`read` / `create` / `update` / `delete`) mirroring the app's configured actions — read-only tables genuinely appear read-only. Each table also carries `context.pages` (which app pages use it) and `operationLabels` (the app's actual button labels: "Add record", "Edit", "Delete").
- An app may connect **multiple distinct data sources**; always call `list_tables` first for the full catalog before concluding data doesn't exist.
- `get_current_user` exists, and combined with the action-scoped catalog this implies the server operates in an **app-user context** rather than the builder identity the workspace server uses (inferred — not confirmed by a live `get_current_user` call).
- **Field keys in records are field IDs, not labels** — same rule as everywhere in Softr DB land; on these servers the mapping tool is `describe_table` (not `database_list_fields`).
- Its `get_schema` returns a **richer field-type catalog than the workspace server's**: creatable types add ADDRESS, PROGRESS, TIME, DATE_RANGE, BUTTON; SELECT documents `choices: array<{id, label, color}>` + `allowToAddNewChoice`; LONG_TEXT documents TEXT|HTML|MARKDOWN formats; ATTACHMENT documents `fileType` + `showAs PREVIEW|BADGE`; PERCENT documents `showAs NUMBER|PROGRESS_BAR|PROGRESS_RING`. Read-only list matches the workspace server.
- **Documented conventions** (unlike the workspace server's silent caps): pagination is `page` (1-based) + `pageSize` (max 100) with `total` and `hasMore` in the response; timestamps are UTC `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` for reads AND writes (the workspace server has used the same format since 2026-10-01); errors return `{code, error, suggestion}` with machine-readable codes (NOT_FOUND, VALIDATION_ERROR, PERMISSION_DENIED, INVALID_REQUEST, INTERNAL_ERROR). Do not assume the workspace server's limits (200-record silent read cap, etc.) transfer here, or vice versa.
- Filter operators, as observed 2026-08-31, used the per-app naming (`GT`/`LT`/`GTE`/`LTE`, `DOES_NOT_CONTAINS`, `IS_WITHIN` relative dates, `IS_ONE_OF`/`IS_NONE_OF`, `HAS_ALL_OF`/`HAS_NONE_OF` (the latter flagged legacy in the schema), `INLINE_CONTAINS`) with per-operator supported-type lists. Per Softr the per-app operator names were realigned on 2026-09-09, so call this server's `get_schema` before building a filter rather than trusting either list — see the schema-drift caution in [Softr Database tools](#softr-database-tools).

**What they are NOT:** a delivery path for blocks. Per-app servers serve a published app's **data** at runtime; they cannot create, edit, or deploy vibe coding blocks — that stays on the workspace server.

## Two delivery paths for this skill

When generating a block, pick the delivery path by what's connected:

1. **WORKSPACE MCP server connected with Applications & Forms full access** (a per-application server does not count — it cannot create or deploy blocks; see the section above) — write the `.tsx` file locally first (it remains the source of truth and the reviewable artifact), then offer to deploy it directly: `vibe_coding_block_create` (or `vibe_coding_block_update_code` for edits), then `vibe_coding_block_connect_data_source` to wire up the data. Verify every push by its `sourceSha256` ([protocol](#verifying-a-push--the-deployed-source-is-the-only-proof)), and remember the action-permissions reset after every code push. A newly created block lands at the bottom of its page, so tell the user to drag it into place in Studio. After deploying, link the Studio page (`https://studio.softr.io/applications/{applicationId}/pages/{pageId}`) and offer `application_preview` / `application_publish` — publish only when asked, and mind the [preview-link auth warning](#application-management-tools).
2. **No workspace MCP (or read-only access)** — classic path: write the `.tsx` file and have the user paste it into Studio's Vibe Coding editor, then connect the data source in the **Source** tab themselves.

Either way, never deliver code inline in chat (JSX character corruption — see SKILL.md workflow step 5).

## When the MCP is not installed

If the user hasn't installed the MCP (and doesn't want to right now), fall back to the schema-discovery methods documented per source:

- **Softr Database:** bundled CLI script — see [../datasources/softr-database.md](../datasources/softr-database.md#bundled-cli-script-get-softr-database); or the `tablespace-with-tables` network paste — see [../datasources/fields.md](../datasources/fields.md#field-inspector-block).
- **Airtable:** bundled `get-airtable-base` script — see [../datasources/airtable.md](../datasources/airtable.md#bundled-cli-script-get-airtable-base).
- **Other sources:** Field Inspector block and vendor workflows in [../datasources/fields.md](../datasources/fields.md#field-inspector-block).
