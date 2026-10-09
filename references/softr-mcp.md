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
- [Application management tools](#application-management-tools) — incl. [condition-based user groups](#condition-based-user-groups) and [testing as any user via "Preview as"](#testing-as-any-app-user-without-logins--the-preview-as-switcher)
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

**Workspace membership is not enough.** The OAuth grant covers only the workspaces ticked on the authorization screen. On 2026-09-01 a user who was a member of a client's workspace in Softr still could not reach it through the MCP; re-authorizing the connector with that workspace ticked fixed it. When an app or workspace you can open in Studio is missing from `application_list` / `workspace_list`, check the grant under Settings → API tokens → Authorized apps.

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

**Set a new block's visibility with `vibe_coding_block_set_visibility` right after creating it, before any further code push.** A new block is visible to All users, and ADD_RECORD's default follows the block's visibility at compile time ([why](#the-array-argument-rejection-and-why-it-is-a-security-issue)). So every push to an ungated block reopens its ADD actions to logged-out visitors: a rebuild's pushes left 28 ADD_RECORD actions at All users (LCDB, 2026-10-05). `customUserGroupIds` is accepted only together with `LOGGED_IN_USERS`, and it narrows that group. Running the app as a user outside an Administrator-only block's group confirmed it: that user did not get the block (impersonation, 2026-10-08). Set groups by id, from `application_list_user_groups`, so a group renamed in Studio later changes nothing on the block (checked 2026-10-07).

**Which read to use** (from the tools' own descriptions, 2026-10-01):

- `vibe_coding_block_get_settings` returns the block's settings, its `actions` (type, `dataSourceId`,
  mapped fields, `permission`, `isDefaultVisibility`) and its wired `dataSources` — everything except
  the source. It is the cheap read before any permission, sort, filter or settings change, and for
  checking what a restore or duplicate kept.
- `vibe_coding_block_get_code` adds the source. Its `dataSources` list is the only reliable answer to
  "is a datasource actually wired to this block?" — the compiler never sees the wiring — and each entry's
  `fieldReferenceKey` (`id` or `name`) says how that source's fields must be referenced in `q.select()`.
- `vibe_coding_block_get_code` with **`includeCode: false`** skips the source text but still returns
  `sourceSha256` and `sourceBytes`. Use it to [verify a
  push](#verifying-a-push--the-deployed-source-is-the-only-proof) (verified live 2026-10-01). It drops
  only the source: the response still carries every data source's field list. It came to about 1 KB for
  a block with few connections, but about 40 KB on a block with 11, and `vibe_coding_block_get_settings`
  was the same size (LCDB QA rounds, 2026-10-08). Read it once after a push, not after every call.
- `vibe_coding_block_list_versions` with **`includeCode: false`** and **`limit: 1`** is the cheap "did
  anything change" read. It returns the newest entry only, with its list id, `versionNumber`, `title`,
  `prompt` and `createdAt`, and no source and no data-source list, so it is far smaller than
  `vibe_coding_block_get_code` or `vibe_coding_block_get_settings` (the sizes above). A QA pass used it
  per block to show that nobody pushed during the run: the newest `createdAt` was earlier than the
  first save (LCDB QA round 2, 2026-10-08). It sees code writes only: a settings-only change adds no
  version, and Source conditions and Action permissions are not versioned
  ([below](#vibe-coding-gotchas-official)). Whether connecting or disconnecting a data source adds a
  version was not tested.
- Push results now report `sourceSha256` and `sourceBytes` too, for the source Softr actually stored.
  A search-replace result also carries `actions`, so one `includeCode: false` read afterwards is enough.
- **"Page not found" from a block tool** means `pageId` and `blockId` were passed the wrong way round, or
  one of them is wrong. Three agents swapped the two (same rounds).

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
3. Several rounds of ops are fine, but **each call is its own push**: it compiles and saves on its
   own. Three things follow.
   - **Every intermediate state must compile.** Replay the ops on the base and gate the text after
     each planned call before you send any of them. Top-down ops can leave a helper undefined
     halfway (only 3 of 54 op prefixes compiled in one plan), so keep the old helper in call 1 and
     delete it in the last call.
   - **Write down the `sourceSha256` each call must return, and check it per call**, not only at the
     end. A mismatch means an op landed differently on one side. The digest describes the source
     Softr stored after merging your edits, not the edits you sent, which is what makes it usable
     here: on this path you never see the merged file yourself.
   - **Each call resets the block's Action permissions and leaves its intermediate code in the
     draft.** Send the calls back to back, re-apply restricted permissions once after the last call,
     then read them back. Anyone who publishes in between ships the intermediate state. In one
     two-call push, an Administrator-only void action was open to any logged-in user for about two
     minutes, between call 1 and the re-apply (LCDB, 2026-10-08). Mark the calls in their
     `versionName` ("… (part 1 of 2)").

**Shrink the ops before you send them.** Trim the common prefix and suffix of each search/replace
pair, then grow the search until it is unique (24 characters or more worked). Check uniqueness in the
state each op applies to: ops apply in order, and only the first occurrence is replaced. Replay the
ops on the base to rebuild the target byte for byte. Smaller payloads mean less text retyped through
the model, and every shrunk push matched its hash on the first try: one plan went from 20,665 B to
10,721 B, another from 19.8 to 16.5 KB, and one header edit's search from 1,173 B to 40 B (LCDB,
2026-10-08). A large insertion needs no full replace: one op anchored on a short unique line carried a
33 KB component, and the returned hash matched the replayed file. On a long one-line header, use a
short unique tail of the line as the search.

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
edits since that push, which is exactly what step 1 below exists to catch. (The digest on push results was first known from Softr's release notes; our own pushes have returned it since at least 2026-10-08.)
Right after that release our client's copy of the tool definition did not declare `includeCode`, so
the argument went out as the string `"false"` and the server still honoured it. Whatever the loaded
definition says, check that `sourceCode` came back `null`.

**The protocol, per block:**

1. **Before editing, prove deployed == disk.** Call `vibe_coding_block_get_code` with
   `includeCode: false` and compare `sourceSha256` and `sourceBytes` to `shasum -a 256 <file>` and
   `wc -c < <file>`. If they differ, the block has changed since your last push: fetch the full
   source, diff it against yours and reconcile. Do not overwrite work you have not seen.
   - **A Studio edit is one cause, not the only one.** Another session or agent can push (and
     publish) in between: a second session pushed to five blocks and published while a QA pass was
     running, which left every scratch copy stale (LCDB, 2026-10-08). And an agent can push, then die
     before it writes the mirror: twice the mirror held a version older than the deployed block, and
     the version history rebuilt what was live.
   - **So compare again at review time and right before the push**, not only before editing, and
     start every edit from the project mirror, never from a scratch copy.
   - **`vibe_coding_block_list_versions` with `includeCode: false` dates every save.** Each entry
     carries its `title` (the `versionName` you passed, or a generated summary) and its `prompt` (the
     `userPrompt` you passed). Pass a descriptive `versionName` and `userPrompt` on every push, and
     the history reads as a log.
2. Edit the local file. Run a parser and `no-undef` lint on it first — `node --check` does **not**
   accept a `.jsx` extension, so use esbuild (`esbuild file.jsx --loader:.jsx=jsx --jsx=automatic
   --log-level=error --outfile=/dev/null`) plus eslint with `@babel/eslint-parser`. The bugs that
   actually bite Softr blocks are semantic — `useRecordUpdate({ select: … })` instead of `fields:`,
   an invented identifier — and the push is the first thing that reports them.
   - **This gate is weaker than Softr's compiler for TypeScript.** esbuild strips types without
     checking them, so a duplicate `type X` passes, and Softr then refuses the push with `Identifier
     'X' has already been declared` (a reviewed block, refused at the second declaration; LCDB,
     2026-10-08). The `jsx` loader cannot parse type annotations at all, so TypeScript source in a
     `.jsx` file needs `--loader:.jsx=tsx`. Add a duplicate-declaration check, for example `tsc
     --noEmit` failing on TS2300, TS2451 and TS2393, and grep the file for each new top-level name
     before you add it.
   - **In any script that asserts a fix, assert on the exact code**, such as `new Date().toISOString()`,
     never on a bare word a comment may also hold: `assert "toISOString" not in out` failed on the
     comment that explained the fix (same pass).
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

**Hash the exact bytes, trailing newline included.** Softr stores exactly the text that reaches it: across
112 push→fetch pairs between 2026-09-09 and 2026-09-30 the fetched
`sourceCode` was byte- and MD5-identical to the text sent, including two pushes sent *without* a
final newline and stored without one. (One thing does not reach Softr as written: a `\uXXXX`
escape in the source arrives decoded, see [below](#unicode-escapes-come-back-decoded).)
The "deployed block is one byte shorter" we chased on
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

**The `versionId` in a push result is the script's build id, not a version-history id.** It is the
segment in the path the page loads, `…/vibe-coding/…/<blockId>/<buildId>/index.js`.
`vibe_coding_block_list_versions` returns `NOT_FOUND` for it, even though that tool's own description
says it accepts a write tool's `versionId`. Every pushing agent in two QA rounds met both ids, and
two looked the build id up in `list_versions` and got `NOT_FOUND` (LCDB, 2026-10-08). The two ids do
two jobs:

- **To prove the preview serves a push**, compare the push result's `versionId` with the build id in the
  served script's URL. [browser-checks.md](browser-checks.md#2-session-preview-cookie-page) (step 2) has the check.
- **To name the version**, use the `versionNumber` from `vibe_coding_block_list_versions`, with its list
  id. Report both ids.

**A push call that times out may still have landed.** Read `sourceSha256` with `includeCode: false`
before you send anything again. A call that answered "server isn't responding" had landed: the
read-back matched the planned hash, and nothing was retried (LCDB, 2026-10-08). A re-sent search-replace
fails on text it already changed, or applies twice where the replacement still contains the search. A
refused push stores nothing, so read the deployed hash back before you send the fix as well. And
when the deployed block, the working copy and the mirror already hash the same, skip the push: every
code write adds a version and resets Action permissions for nothing (a no-op push skipped this way
in the same rounds).

**Do not read a 100KB block into a model's context to push it.** The full-replace tool takes the
whole file as a string parameter, so the source has to pass through whatever is making the call.
Verification no longer has to: the digest is a few hundred bytes (the read that returns it can be larger on a block with many data sources, [above](#vibe-coding-block-tools)). A large multi-block deploy is still
safer farmed out one file per subagent — a fresh context per file means no compaction can land
mid-file — and the hash comparison is what makes that delegation safe, not trust in the agent. The
steps that need judgement are the *edit* and the *review of the diff*; the hashing, the compare and
the push itself are mechanical, and can run on the cheapest tier available without lowering the bar,
because a wrong result fails loudly rather than plausibly.

**What a push also resets.** Every code push puts the block's derived Actions back on Softr's
default permissions (see the next section for why that can be a security problem and how to verify
the restoration). If page-level visibility is the access control in your app, record that decision
so nobody chases the reset after every round; if it is not, re-tighten and read back.

**What a push leaves alone, and when it goes live** (our observations on Softr Database, not
from the docs):

- **A code push does not clear Source conditions** (verified 2026-09-18). Only the Actions reset.
- **Disconnecting and reconnecting a data source does.** `vibe_coding_block_disconnect_data_source`,
  then `vibe_coding_block_connect_data_source` with the same table, brings the block back bound to
  that table with an **empty** condition (2026-09-10). Other blocks bound to the same data source id
  kept theirs. That makes it a way to clear a broken condition when the filter tool cannot be called,
  and it also means a reconnect done for any other reason drops the row gate: read the conditions
  back afterwards. The next code push re-derives the block's Actions at the defaults, as any push does.
- **A push lands in the draft.** The live app serves it only after the next app publish, and that
  publish, whoever runs it, takes every other pending draft change live with it, unversioned
  settings edits included. Before calling a block "staged", compare the app's last publish time
  (`application_get`) with the version's `createdAt` (`vibe_coding_block_list_versions`): on
  2026-09-01 a block we believed staged went live with a publish 28 minutes after it was saved.

#### Unicode escapes come back decoded

Verified 2026-10-08 on a large dashboard block pushed in stages with `vibe_coding_block_update_code`
and `vibe_coding_block_update_code_search_replace`: exactly the calls whose text held a JavaScript
`\uXXXX` escape came back with a `sourceSha256` that differed from the hash of the planned text. The
block's accent-folding regex, `/[\u0300-\u036f]/g`, was stored with both escapes replaced by the
characters themselves, two combining marks sitting raw between the brackets. `\d`, `\D` and `\s` in
the same block arrived as written.

The decoding happens somewhere between the tool call and storage (the client's JSON handling of
the argument, or the server), not in Softr's compiler: the stored source text itself changed. It
looks like the [encoding trap](#which-edit-tool-full-replace-vs-targeted-search-replace) above,
reaching a backslash-u that was meant to stay in the source. The exception is a lone surrogate:
`\udc00-\udfff` in the same regexes has no character form, and those pushes stored it unchanged.
(The `\u{…}` form is untested; treat it the same.)

**So: no `\uXXXX` in pushed source, lone surrogates aside.** Find them before a push with
`grep -n '\\u[0-9a-fA-F]\{4\}' <file>`, then either:

- **Write the characters themselves**, with a comment saying why, since combining marks and other
  invisible characters cannot be read in an editor. Spell "backslash-u" out in that comment so it
  holds no escape either. Check first that the character means the same raw in that spot: a range
  of combining marks in a character class does (the block's regexes, escaped and raw, matched the
  same set across all 65,536 BMP code points), but written raw, a `/` ends a regex literal, a `]`
  closes a class, a backslash or quote changes the token, and U+2028/U+2029 are line terminators a
  regex literal may not contain.
- **Build it from code points** where a raw character is unwanted or unsafe:
  `new RegExp("[" + String.fromCharCode(0x300) + "-" + String.fromCharCode(0x36f) + "]", "g")`,
  created once at module scope. No backslash-u reaches the tool, so there is nothing to decode.
  Strings likewise: `String.fromCharCode(0x2014)`, not `"\u2014"`.

If a push has already stored the decoded form, applying the same replacement to the mirror brings
the hashes back together; confirm the raw characters behave the same (first bullet) before calling
it done.

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
impersonated users, direct POSTs).* A block's data lives behind per-connection endpoints, and these
are the gates that actually exist on them. Which name sits in the path matters when you read a network
log or write a request guard:

- **In a block that declares `datasource.define`, reads use the define name** (HubSpot capture,
  2026-10-05; Softr Database capture, 2026-10-08). A list is
  `POST …/blocks/<blockId>/datasources/<name>/records`, and one record is
  `POST …/datasources/<name>/records/<recordId>`. A `*/datasources/*/records` pattern does not match
  the single-record read.
- **Writes do not use the name.** A create is `POST …/datasources/<uuid>/records-trigger/new`, and an
  update is `PATCH …/records-trigger/<recordId>`. The uuid differed between runs (in the HubSpot capture
  it changed on recompile), so key write guards and log filters on `records-trigger`, never on the name
  or the uuid.
- **One earlier capture is not explained by this.** A 2026-09-18 Softr Database capture recorded a
  read under the connection's id. That case (possibly a block without `datasource.define`) was not
  re-checked.

The gates:

| Gate | Enforced server-side? |
|---|---|
| **Page VIEW permission** | **Yes.** A viewer who cannot view the page gets **403** ("block/action visibility rules…") from the block's datasource endpoint — crafting the request by hand does not get around it |
| **The block's Visibility** (`predefinedUserGroup` + `customUserGroupIds`; `vibe_coding_block_set_visibility`) | **Yes.** A viewer outside the block's group gets the same **403**, on list and by-id, even where the page lets them in. The body reads like a write error on a read: "You cannot add or edit a record because either the block/action visibility rules, user group conditions, or the user/record data in the datasource has changed." Per block: the same table on an ungated block stays open. Five code pushes left the setting intact |
| **The connection's Source conditions** (Source tab / `vibe_coding_block_set_data_source_record_filters`) | **Yes — and they are the only server-side ROW gate.** A by-id request for a record the condition excludes answers differently per backend: **HTTP 200 with an empty body** on Softr Database (2026-09-18), **404** on HubSpot (2026-10-05). Treat both as "not found" |
| A `where` filter in the block's code | No — it is a request parameter the caller controls. It can also **fail open**: on 2026-09-19 (Softr Database) a request filter on a field that was not in the connection's read-select union was silently ignored, with no error, and the query returned everything. Confirm the filtered field is selected on the connection and prove the `where` narrows the result (compare counts with and without it); see [reading.md](../datasources/reading.md#filters-fail-open). A `where` naming an alias missing from its own hook's `select` fails the other way and crashes the block (Hard Constraint 29) |
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

**Saves carry the page URL.** Every save body holds `context.pageURL` and `context.URLParameter`. A
value a block keeps in the URL, such as a `?q=` search holding client names, therefore goes to Softr's
server with every save on that page (seen on a blocked save, 2026-10-08). Decide on purpose whether
such a value may sit in the URL, and record the decision.

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
- **Do not confuse it with the user-group syntax.** A user group's condition names the user field
  as its **subject**, `USER:<field id>`: one colon, no braces (verified 2026-10-07, see
  [Condition-based user groups](#condition-based-user-groups)). A Source condition names it in the
  **value**, `USER:::<field id>`: three colons. The user-group form returned HTTP 400 in a Source
  condition (below); the Source-condition form has not been tried in a user group.
- **Use AND between rules.** With one rule OR and AND behave the same, but a second rule added
  under OR widens access (2026-10-05).
- **The braced user-field spellings fail.** On 2026-09-18, on Softr Database, eleven spellings were
  tried, including `{USER:::<fieldId>}`, `{USER:<fieldId>}` and `{USER:::FIELD:<fieldId>}`. Each
  silently matched nothing. All eleven had braces, so the braceless form is untested on Softr
  Database, not disproved. A subject of `USER:<fieldId>`, the syntax user-group rules use, returned
  HTTP 400 "Field not found": the user field goes in the value, never the subject. No token that
  tests whether the user is in a group has been found.
- Studio's conditional-filter UI offers the logged-in user's Email and Email-Domain, plus every
  users-table field once users sync from a data source (documented). For a value not listed here,
  pick it in a block's Source tab, save, and read `dataSources[].condition` back with
  `vibe_coding_block_get_settings`. That is how the user-field form was found.
- **CONTAINS against a list of emails has a substring trap:** `bob@x.com` matches a field holding
  `jbob@x.com`. Prefer IS against a single-email field, and remember that an EMAIL-typed field can still hold a list ([../datasources/softr-database.md](../datasources/softr-database.md#gotchas)). If a record must hold several emails, the
  delimiter trick the embedded form was meant to provide does not work, so accept the trap or
  split the data.
- When a row gate must follow something other than the user's email (a company, a team), compare
  the record's field with the user's own field through `USER:::<user field id>`. Where that form is
  untested (Softr Database so far), store an email on the record and compare it with
  `{USER:::EMAIL}`. Staff who need every row get a group-gated block with unfiltered connections
  ([above](#what-the-server-enforces-on-a-blocks-data-endpoints)), not a wider condition.
- **A Softr Database recipe for "everyone named on the record, plus staff"** (verified 2026-09-18
  in a production app):
  - `CONTAINS` is a case-insensitive **substring** test. It works against a FORMULA text field and
    against a LOOKUP of one (subject `type: "TEXT"`). So a formula that joins every email on the
    record (lower-cased, comma-delimited) gates rows with `<formula> CONTAINS {USER:::EMAIL}`,
    substring trap included (above).
  - Related tables follow the parent through a LOOKUP of that formula, with the same condition on
    the lookup.
  - A LOOKUP that brings an email over a link field works with `IS_ONE_OF {USER:::EMAIL}`.
  - There is no group token, so a **constant** formula listing the staff emails stands in for one:
    `<access formula> CONTAINS {USER:::EMAIL}` OR `<staff formula> CONTAINS {USER:::EMAIL}`. This is
    the OR widening warned about above, chosen on purpose. A staff-only connection carries the
    second rule alone. Adding a staff member then takes two edits: the user group and the formula.
  - The MCP cannot edit a formula after creation, so the staff list is changed in Studio.
  - `vibe_coding_block_set_data_source_record_filters` takes one flat level: the rules joined by a
    single AND or a single OR, no nested groups.

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

Ours, not from the docs: **Source conditions and Action permissions are not versioned.** The version
history cannot date a change to either (noted 2026-09-10). Whether restoring a version brings back an
older condition we have not tested. What a code push does and does not reset is in
[Verifying a push](#verifying-a-push--the-deployed-source-is-the-only-proof).

## Application management tools

The Applications area goes well beyond reads (roster as delivered 2026-10-01; behavior not individually exercised unless stated):

| Group | Tools |
|---|---|
| Apps | `application_list`, `application_get`, `application_create` (create a whole app via MCP), `application_set_name`, `application_set_subdomain`, `application_set_domain`, `application_set_login`, `application_configure_sign_up`, `application_configure_email_sender`, `application_update_data_source` (point/swap the app's data source), `application_update_pwa_settings` (installable-app name, short name and theme colour; new 2026-10-01) |
| App users and groups | `application_list_users`, `application_add_user`, `application_remove_user`, `application_set_user_activation`, `application_list_user_groups`, `application_create_user_group`, `application_update_user_group`, `application_delete_user_group`, `application_create_user_connection`, `application_get_user_connection`, `application_remove_user_connection` |
| Pages / blocks / permissions | `application_page_list`, `application_page_get`, `application_page_create`, `application_page_get_block`, `application_page_get_permissions`, `application_get_access_overview` (user groups plus counts of redirections and data restrictions) |
| Publish / preview | `application_preview`, `application_publish` |
| Workspace | `workspace_list`, `workspace_list_email_senders`, `get_workspace_integrations` (distinct from the [integrations drill-down](#browsing-integrations-external-data-sources) below) |

**Email senders, as the MCP shows them** (read 2026-09-10 and 2026-09-18): `workspace_list_email_senders` lists each workspace sender with a `confirmed` flag, and an address that was added but never verified reads `confirmed: false`. `application_get` showed the app's own sender as `<subdomain>@softr.app`. In a workflow, a `SOFTR_SEND_EMAIL` node chooses its sender through the optional `emailSenderSignatureId` input. Before publishing a workflow that must send from a particular address, check that the address is in the list and confirmed.

**Three setup facts from an app build** (LCDB, 2026-10-05 to 07):

- **A plan caps its custom user groups, so check the cap before designing roles.** The app's public config, `window.application_context` on its `/login` page, carried `numberOfCustomUserGroups` (3 on that plan) and `signUpSettings.policy`. It is a read-only check and needs no login. The cap forced a late redesign from four groups to three.
- **A new app comes with a default test user** (`testuser@example.com`, seen in the one app we created) in no group. Deactivate it before go-live, or keep it as the no-group test account.
- **After a subdomain change, the old address returns 404 with no redirect**, so every old link is dead. Re-read `application_get` afterwards for the app's email sender, which showed the subdomain-based address before the change. Whether the sender follows the change was not checked.

Combined with the database tools (`database_create` / `database_create_table` / `database_create_field`) and `vibe_coding_block_create` + `application_publish`, the tool set for scaffolding a full app end to end now exists. (Existence-verified only — that pipeline hasn't been run live; treat the first full scaffold as an experiment, not a routine.)

**Etiquette from the server's own instructions:** after changing a block, link the page as `https://studio.softr.io/applications/{applicationId}/pages/{pageId}`; offer `application_preview` or `application_publish`, but **only publish when the user asks**.

> **application_preview links are auth tokens.** Per the server's own instructions, a preview link **signs its opener in as the user who requested it** and lasts about a day. Give it only to that user, and mint a fresh one with another `application_preview` call rather than re-sending an old link. Never paste a preview link into a shared channel.
>
> **The `&version=<n>` in a preview link is an app-level number, not a block version, and it does not prove which code is served.** By Softr's design a link keeps serving the version it was minted for, but in one app every freshly minted link read the same `&version=153` for about 16 hours, across dozens of block pushes and two app publishes, and each link served the newest block build (LCDB QA pass, 2026-10-07 to 08). Prove what is served by the script's build id, as in [the `versionId` note](#verifying-a-push--the-deployed-source-is-the-only-proof). After every push, still mint a new link (or press the preview's `#refresh-button`) before you check anything. Whether a link minted *before* a push keeps serving the old build was not re-tested.

**Reading pages and blocks:**

- `application_page_get` lists a page's blocks **in page order, with no `order` field**. That field
  was always `null` and was removed on 2026-10-01 (verified live that day; the tool's description
  still mentions it). For a block nested in a column or tab container, the container's slots set its
  position, not its place in the list. The list is not visual order where shared blocks are involved
  either: it showed the shared navigation header block after the page's content on every page except
  Home, in two apps (LCDB, 2026-10-05 to 08).
- **A block created over MCP still lands at the bottom of the page**, and no tool places or reorders
  blocks yet. Softr has said placement will come later. Until then, a human drags it into place in
  Studio. Say so when you hand the block over.
- **Studio-only jobs, with no MCP tool** (checked against the roster of 2026-10-08):
  - setting a page's VIEW permissions (`application_page_get_permissions` only reads them);
  - Page Rules, which are not readable either (`application_get_access_overview` gives only counts of redirections);
  - navigation links (`application_page_get_block` on the shared Navigation block does not return them);
  - renaming a block (a block deployed into a new page's placeholder keeps the title "Vibe coding block");
  - the app's Custom Code and theme.
- **Before a human deletes a user group, prove it unused.** First by id over MCP: block visibility,
  action permissions and page permissions. Then in Studio, where the MCP cannot see: Page Rules rows
  and navigation-link visibility. A group that came back clean on both was deleted by hand
  (LCDB, 2026-10-07).
- **Timestamps are UTC with a `Z`.** Since 2026-10-01, timestamps such as `publishedAt` or a
  version's `createdAt` are ISO-8601 UTC with millisecond precision, studio-side and tables-side
  alike (per Softr; verified on `vibe_coding_block_list_versions` that day). Before then, studio-side timestamps came back with
  no zone designator and nine fractional digits (`2026-09-09T22:34:11.157881061`). They were UTC, so
  read any older logged value as UTC, never as local time.

### Condition-based user groups

*Verified 2026-10-07 on Softr Database, with users synced from a Softr Database table and the user
connection's field reference key set to `id`. The HubSpot version (2026-10-05) is in
[../datasources/hubspot.md](../datasources/hubspot.md#user-sync).*

- **`application_update_user_group` sets a group's condition.** It returned the condition exactly as
  sent. This one, on a "Volunteer" group, tests two single-line text fields of the users table:

  ```json
  {
    "logicalOperator": "AND",
    "expressions": [
      { "subject": { "field": "USER:YB2ot", "type": "TEXT" }, "operator": "IS_NOT_EMPTY", "value": [] },
      { "subject": { "field": "USER:uo0TW", "type": "TEXT" }, "operator": "IS", "value": ["Active"] }
    ]
  }
  ```

- **The subject is `USER:<field id>`: one colon, no braces.** A block's Source condition uses a
  different form, `USER:::<field id>` with three colons, and puts it in the value
  ([Logged-in-user values in Source conditions](#logged-in-user-values-in-source-conditions)). Do not
  copy one into the other.
- **`application_list_users` does not show condition-based membership.** Right after the update, the
  one user whose record matched (login email set, status Active) still listed `userGroups: []`. The
  tool shows only manual memberships, such as a user added to Administrator through `userEmails`.
  Softr evaluates conditions at runtime, so an empty `userGroups` there is not evidence that a
  condition fails. HubSpot behaved the same way.
- **Check membership by running the app as that user** and reading the groups the app gives them
  ([how](#testing-as-any-app-user-without-logins--the-preview-as-switcher), below).
- **After any group change, in Studio or over MCP, read the groups back with
  `application_list_user_groups`.** A group left in condition mode with nothing filled in reads back as
  a condition holding one blank rule (no field, no operator). What that rule matches is unverified, so
  switch the group to a manual list before anyone relies on it. A read-back found this on a group
  that was meant to be manual (LCDB, 2026-10-07).
- **Keep the top administrator group a manual list.** A condition on users-table fields hands
  membership to anyone who can edit those fields in the table, so they could promote themselves.

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
- **Read a user's groups from the app itself** (verified 2026-10-07, read-only). Mint a fresh
  `application_preview` link and open it, run the impersonate call above, reload the app iframe,
  then read `iframe.contentWindow.__softr_current_user.userGroups`.
  - The link carries `?show-toolbar=true`, so the top document is the toolbar shell and the app runs
    in `document.querySelector('iframe')` (the `#preview-iframe` of
    [browser-checks.md](browser-checks.md)). In the shell, `window.__softr_current_user` exists only
    in that iframe's `contentWindow`; the shell itself has no user globals.
  - **On a page URL opened directly on the preview origin, the app is the top window**, and
    `window.__softr_current_user` (email and groups) is readable there (verified 2026-10-08, for an
    administrator and a volunteer). That is the flow [browser-checks.md](browser-checks.md) uses.
  - To reload, set the iframe's `src` again with a fresh `t=<timestamp>` query parameter, after the
    impersonate call. On a direct page URL, reopen the page instead.
  - **Read the email and groups after every switch, before any role check.** The impersonate fetch
    returns 200 while the already-open page keeps the old user, until the page is reopened. A mistyped
    id returns 400 and the preview silently stays as the previous user, so a role check can run as
    the wrong person without any error (2026-10-08).
  - Observed group names: a user who matched the Volunteer condition above read
    `["Logged in users", "All users", "Volunteer"]`; a user with no login email read
    `["Logged in users", "All users"]`.
- **`window.__softr_current_user` carries only `name`, `email`, `avatar` and `userGroups`**
  (verified 2026-10-07). None of the users-table record's other fields were there, on a users table
  with notes, phone and emergency-contact fields. For a privacy review: syncing a users table does
  not by itself expose the record's other fields through this global. A block can still ask for
  them with `useCurrentUser({ properties })`
  ([../datasources/reading.md](../datasources/reading.md#current-user)).
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
- **`database_create_field` for a DATETIME takes `options: {"includeTime": true}`** (ours, verified
  2026-09-18). The options shape `database_list_fields` returns for an existing DATETIME field is
  rejected, so do not copy a field definition from a read into a create.
- **A formula cannot be changed after creation.** `database_update_field` with a new `formula` is
  refused: `BAD_REQUEST` "[formula] can only be set when the field is created; delete the field and
  create it again to change it" (seen 2026-09-18, under the old name `update_field`). Edit the formula
  in Studio instead.
- **SINGLE_LINE_TEXT fields carry a 1,024-character `maxLength`** (ours: two fields of a production
  table, found in a 2026-09-10 schema audit and confirmed live 2026-09-18, recorded in a block's code
  comment). A block that appends to such a field has to keep the total under it; what a longer write
  does was not tested. Use LONG_TEXT for anything that grows.
- Limits: 100 records per `database_create_records` call, 200 records per read (silently capped, not an error), 2 group-by fields in `database_aggregate_records`. For big tables prefer a filter or aggregate over paging. The read cap is per call, not a ceiling: `database_list_records` takes `offset`, and on 2026-09-01 `limit` 200 with `offset` 0 to 2,400 read a 2,549-row table in 13 calls, every record id unique, no gap or overlap (ours).
- **`database_aggregate_records`: one metric per call, and prove every filter narrows** (ours, LCDB,
  2026-10-08, both rounds of a QA pass). Two metrics in one call were refused more often than not.
  In the first round, two metrics on different fields returned `BAD_REQUEST` every time, and a SUM
  and a COUNT of the same field worked once. In the second round a SUM and a COUNT of one field
  returned `BAD_REQUEST`, with and without `displayFormat`, and so did a COUNT added to a grouped SUM
  call; yet a SUM grouped by MONTH alone (no `displayFormat`) or by one field worked, and so did one
  call with a COUNT of a second field, the date, beside the SUM. Group-by acceptance was
  inconsistent across agents on the same day too: SELECT and CHECKBOX were refused, while text,
  LINKED_RECORD, DATETIME by MONTH and DISTINCT on a link each worked in one run and returned
  `BAD_REQUEST` in another. So prefer filter-only, single-metric calls (one per value or range), and
  check that the parts add up to the unfiltered total. A filter in a shape the tool does not expect
  (`{logicalOperator, conditions}`) was ignored with no error, and the count came back as the whole
  table. The tool expects `{ condition: { operator: "AND"|"OR", conditions: [...] } }`, with field ids
  in `leftSide`. Compare every filtered count with the unfiltered one. To leave out rows flagged by
  a checkbox, filter `IS_NOT true` instead of grouping by it.
- **`database_search_records`:** filters name fields by id in `leftSide`. A sort on `updatedAt` was
  silently ignored, and a filter on `id` was rejected.
- **`database_create_field` on a LINKED_RECORD always creates a single-valued inverse** on the target
  table, named after the source table. Links defined inside `database_create_table` got none (LCDB,
  2026-10-05). Make the inverse multi-valued (`database_update_field`, `options.allowMultipleEntries:
  true`) unless one-to-one is meant. Otherwise a second link silently overwrites the first, as in
  [the single-valued pair trap](../datasources/writing.md#linked-record-write-traps-verified-live-2026-08-26).
- **On the workspace server, a new database starts with a starter table, "Table 1"** (Name, Description
  and Status fields). Per the `database_create` tool's own description (checked 2026-10-08), the vibe
  coding application endpoints create it empty instead. Reshape the starter table with
  `database_update_table`, `database_create_field` and `database_update_field` rather than adding a
  table beside it. A database holding it is not empty, so `database_delete` refuses it without `force`.
- **`database_create` rejected a description with `BAD_REQUEST` once** (2026-10-05). If it does,
  create the database without one.

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
- **`CUSTOM_CODE`:** runs custom **JavaScript or Python** inside a workflow. Its input and output contract (an object `inputData`, the result under `$.body`) is the `CUSTOM_CODE` bullet in the build-loop findings below.
- **AI actions:** Softr AI, OpenAI, Anthropic, Gemini, and Mistral each ship Write / Summarize / Categorize / Custom-prompt nodes; OpenAI adds gpt-image-2 image generation. Pinecone, Firecrawl, Replicate, and Linkup nodes exist too.
- **Integration apps (top of 56):** Stripe (36 nodes), QuickBooks (24), ActiveCampaign (23), SharePoint (22), Asana (18), Gmail/Attio/Brevo/Resend (12 each), ClickUp/Zendesk (10), Airtable/Notion/Cal.com/HubSpot/Xero/DocuSign/Apollo (9 each), Sheets/Excel (8), monday/SQL/Jira (7), Slack/Telegram (6), plus Salesforce, Coda, Calendly, Twilio, Zoom, Linear, Trello, form tools (Typeform/Tally/Jotform/Fillout), and more.

**Mechanics from the server's own instructions:**

- Node inputs can embed **references to another node's runtime output**, a loop's current item, or named date/time tokens.
- **Test-first is mandated:** every testable node needs a test run before its outputs become referenceable by downstream nodes. Each node carries a `testRunMode` — `REAL_ONLY`, `MOCK_ONLY`, or `MOCK_AND_REAL` — so some nodes can only be tested against real side effects while others mock. See the test-safety rules under build-loop findings below before testing anything against a production workspace.
- **Workflows are owned by a workspace, and can now be pinned to an app** (verified 2026-10-05 from the tool definitions). `workflow_create` still requires a `workspaceId`; its optional `applicationId` "pins the workflow to it, so it is listed on that app's Workflows tab", and `workflow_list({ applicationId })` lists the workflows pinned to an app. Leave `applicationId` out for a workflow that belongs to the workspace as a whole. Pinning or not, `application_preview` / `application_publish` do not apply to workflows. Link a workflow as `https://studio.softr.io/workflow/{workflowId}`.

**Build-loop findings (verified live 2026-09-01, first end-to-end production build — 10 workflows; bullets dated later come from a second production build, 2026-09-18/19):**

- **`workflow_create` instantiates an OLD version of the trigger node.** Immediately call `workflow_replace_trigger_node` with the **same trigger type** — the replacement lands at the current version with the current inputs. Example: `updateField` on `SOFTR_TABLES_RECORD_UPDATED` (fire only when a watched field changes; it takes an UPDATED_AT-type field, see "Trigger scope" below) only exists at v1.2.0; the version `workflow_create` instantiates doesn't have it. Do it before anything references the trigger: the replacement gets a **new node id** (see the `workflow_replace_node` bullet below).
- **A Workflow FILTER node's condition written over MCP is inert — set it in Studio** (corrected 2026-10-06; this bullet used to say the MCP writes it). This is about the Workflows FILTER node only. A block's Source condition written with `vibe_coding_block_set_data_source_record_filters` **is** enforced (verified 2026-09-18 and 2026-10-05, [above](#what-the-server-enforces-on-a-blocks-data-endpoints)), so do not route it to Studio. A project agent once applied this rule to a block's Source filter and routed it to Studio for nothing. `workflow_update_node_inputs` with inputName `"condition"` accepts an `{operator, conditions: [...]}` object and stores it in the node's `inputs.condition`, a field the engine does not read. The engine evaluates the condition on the FILTER node's **outgoing path** (the `paths` entry whose `fromActionId` is the filter), and only the Studio builder writes that. **A filter built over MCP passes every run.** A 2026-09-19 audit of this very build showed it three ways: the one workflow actually running had empty `inputs` and its whole condition on the path; two others, edited in Studio afterwards, held one condition in `inputs.condition` and a different one on the path, so Studio reads and writes only the path.
  - **The official MCP docs agree:** "Branch and filter conditions can't be set through MCP yet ... deciding what sends a run down each path is something you finish in the builder" (docs.softr.io/mcp/workflows, checked 2026-10-05), and the FILTER spec declares `inputs: {}`. BRANCH conditions were not tested separately here; treat them the same way.
  - **How to build one:** add the FILTER over MCP if that is convenient, then open it in Studio, set its clauses and save. Never trust `inputs.condition` as a record of what the filter does; it can disagree with the path.
  - **How to check one:** read the workflow back with `workflow_get` and find the `paths` entry whose `fromActionId` is the filter; the condition must be there. FILTER nodes cannot be run with `workflow_test_node`, so this read-back is the only check before a real run.
- **`LOOP_ACTION_GROUP`'s `loopVariables.items` must reference a plain array**, e.g. `$.records` — a `[*]` projection (e.g. `$.records[*].fields.X`) is rejected by the validator. Per-item references **inside** the loop use `{loopActionGroup.<id>:::loopVariables.items.fields.<fieldId>}` (use the bracket form for ids that start with a digit).
  - **Over a plain array of strings** (a `CUSTOM_CODE` node's `$.body.<key>`, say), the item *is* the value: reference it as bare `{loopActionGroup.<id>:::loopVariables.items}`, nothing after `items` (2026-09-19; accepted by the validator, not yet exercised by a run).
  - **References into the loop are rejected until the source node's saved sample holds at least one item** (the validator says so). Test the source node on a record that yields a non-empty array before wiring the steps inside the loop.
  - **To put a step inside the loop**, call `workflow_add_node` with `compositeNodeId: <loopNodeId>`. The step lands in the loop's own `actions` / `paths`, not the workflow's.
  - **The loop has a `loopCounter` input**, `{ start, end, step, maxIterations }`. `maxIterations` can be set over MCP and reads back (2026-09-19). We have not run a loop long enough to reach the cap.
  - **An empty loop does not stop the run** (recorded 2026-09-19). Zero items means zero iterations and a normal completion, and the steps after the loop still run. A guard stamp placed after a loop therefore fires even when nobody was emailed, and consumes the notice. A gate on the item count has to cover the loop and the stamp together; gating only the stamp leaves the guard unset, and the next edit sends again.
- **`workflow_update_node_inputs` batches validate against the STORED node state**, not the batch-in-progress — an update that depends on another update in the same batch fails validation. Split dependent updates into sequential calls.
- **`CUSTOM_CODE` contract** (2026-09-18/19; found by testing, documented nowhere we know of):
  - `inputData` must be a JSON **object**, name → value. The `[{key, value}]` shape other `KEY_VALUE_MAP` inputs take fails the run with `script_args must be an object.`
  - The code reads `inputData.<name>` and ends with a top-level `return { … }`; the body runs wrapped in a function.
  - **The engine wraps what you return:** the node's output is `{ body: <returned object>, statusCode: 200 }`, so downstream references read **`$.body.<key>`**, never `$.<key>`.
  - **The order of `inputData` keys is not kept.** The stored map came back reordered (2026-09-19). If the code must read some inputs after others, order them in the code (by key name, say), and assert on sets and counts in tests, not on order.
  - **There is no native split / list / array-from-text step.** `workflow_list_node_types` has none, and `TRANSFORM_DATA` takes per-field formulas rather than producing a list. Turning a text field of comma-separated addresses into an array a loop can walk takes a `CUSTOM_CODE` node.
  - Testing it: see the test-safety rules below.
- **Reference validation runs against saved samples** (2026-09-18/19). `workflow_update_node_inputs` checks every `{outputs.<nodeId>:::$.path}` reference against the referenced node's **saved test sample** and rejects a path that does not resolve there: `path "$.fields.<fieldId>.label" does not resolve against node "…"'s sample output`. A record trigger's sample is not yours to choose: re-running `workflow_test_node` on the trigger returns the same record every time. If that record has the field empty (a blank SELECT has no `.label`), the reference cannot be written over MCP at all. Studio's variable picker offers the path regardless of the sample, so add such a reference in Studio.
- **Pass link fields bare.** A `[*].label` projection on a link field (`$.fields.<linkId>[*].label`) does not resolve when the link is empty, and kills the node. Pass the bare field (`$.fields.<linkId>`) into a `CUSTOM_CODE` node and read the labels in code (2026-09-19).
- **`workflow_replace_node` swaps a node's type in place and gives it a new node id** (2026-09-19). The node keeps its place in the graph, which is how a step can be rebuilt as a different type without deleting anything, but every `{outputs.<old id>:::…}` reference to it now points at nothing. Before replacing a node, read the workflow with `workflow_get` and search every input for its id: a node whose output is interpolated into an email body would leave those values blank. `workflow_replace_trigger_node` does the same to the trigger (2026-09-18): new id, so every reference to the trigger has to be re-pointed and the trigger re-tested, which is why it belongs right after `workflow_create`. Both leave the discarded node's sample behind in `nodeSamples`. Nothing references it and it changes nothing, no tool removes it, and it is not evidence that the current node was ever tested.
- **A workflow's own record write re-fires its record-updated trigger** (seen on a production workflow, 2026-09-01). When the trigger watches the table's last-modified field, the workflow's final write is itself an edit. Two guard patterns, both used in our builds:
  - **A send-once stamp:** a "…Sent" date field that the filter requires to be empty, written once at the end, outside any loop. It is the dedupe and the loop guard in one.
  - **Clear the request in the same write:** when the trigger reacts to a request field, the write that acts on it also empties it (`CLEAR_VALUE`), so the re-fire finds nothing to do.

  Never remove the guard, and never relax the filter to something that stays true after the write. The filter itself has to be set in Studio (see the FILTER bullet above).
- **Trigger scope** (2026-09-18):
  - `SOFTR_TABLES_RECORD_UPDATED`'s optional `updateField` takes a field of type **UPDATED_AT** (a last-modified field), not any field. A table without one cannot set it, and the trigger then fires on every edit of every record. It is a plain select input: `workflow_get_dynamic_input_options` rejects it.
  - **A workflow has exactly one trigger**, and "Record added" (`SOFTR_TABLES_NEW_RECORD`) and "Record updated" (`SOFTR_TABLES_RECORD_UPDATED`) are separate trigger types, so reacting to both takes two workflows. Whether creating a record also emits an "updated" event is unknown; make the pair idempotent so it does not matter.
- **Record-write field modes** (written over MCP 2026-09-18). Each field in a Softr Database record write carries a `modificationType`. `ADD_VALUE` adds to a multi-value field (multi-select, multi-link) and keeps what is there; `REPLACE_VALUE` overwrites the whole value, so on a multi-link it drops every earlier link; `CLEAR_VALUE` empties the field (sent with `value: ""`). Use `ADD_VALUE` to give a record one more link or option. These write steps have not run yet (testing one performs the real write), so how `ADD_VALUE` treats a value that is already present is unverified.
- **`serialExecution: true`** in a workflow's configuration (set with `workflow_update_configuration`, confirmed by read-back, 2026-09-18) makes runs queue instead of overlapping. We set it on a workflow that appends to a multi-link field: two runs at the same moment would each read-modify-write the same array, and one append could be lost.
- **`continueOnError` is stored on the path, not on the node** (2026-09-19). Turned on with `workflow_update_node_continue_on_error`, it shows up as a `SUCCEEDED OR FAILED` condition on the node's outgoing `paths` entry. Without it a failed step ends the run, so a guard stamp after it never happens and the whole notice goes out again on the next edit. On the **last step inside a loop** the entry has the condition but **no `toActionId`**, and whether the engine reads that as "carry on with the next item" is unproven. Test it with one deliberately bad item mid-list and check that the items after it still ran.
- **Time-based sends** (a proof of concept, 2026-09-01): a formula field flips (to `"yes"`, say) on the target day, a filtered view picks up the records where it has flipped, and a "Record enters view" trigger fires when one enters.
- **Each workflow has its own `configuration.timeZone`.** In one workspace every MCP-built workflow read `UTC` and an older one `Europe/Athens` (2026-09-19). Read it with `workflow_get` before relying on dates, times or a time-of-day window inside a workflow.
- **Read publication state from `workflow_get`.** A workflow that was never published reads `enabled: false` and `enabledVersion: null` (2026-09-01); the one running workflow in the same workspace read `enabledVersion: 0` (2026-09-19).
- **Test-safety rules** (which `testRunMode` means what in practice):
  - Record-**write** nodes (`SOFTR_TABLES_UPDATE_RECORD` etc.) are `REAL_ONLY` — **never test them against a production workspace**; the test performs the real write.
  - `SOFTR_SEND_EMAIL` is `MOCK_AND_REAL` — **always pass `mode: "mock"`**.
  - Triggers and `GET_RECORDS` are `REAL_ONLY` but read-only-safe; a record-updated / enters-view trigger test just samples an existing record.
  - `CUSTOM_CODE` is `REAL_ONLY` too, but a node whose code calls no integration and writes nothing is safe to test, and testing it is how you get the non-empty sample later references need (2026-09-19).

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
