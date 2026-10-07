# HubSpot

*Rewritten 2026-10-05 from a read-only verification run: five investigations and four adversarial
fact-checks against a HubSpot-connected demo app on an EU portal, plus Softr's and HubSpot's live
docs. Labels used below: **verified live** = observed that day through the Softr or HubSpot MCP,
in the browser's network log, or in a test block's own output in the preview; **documented** =
Softr or HubSpot docs say so; **inferred** = reasoned, not observed; **unverified** = nobody has
tested it. That run made no writes. Write tests followed that day, all in Studio preview
("Preview as": the builder's session acting as the chosen user, not a real login). In the
morning a test block created a ticket with company and contact links and then re-linked it. In
the afternoon the Accounts block changed the stage of that ticket and of one test deal, and a
client's replay of one of those requests was refused. On the write side, only what those tests
covered is verified live.*

## Overview

CRM used as a Softr data source, connected by OAuth.

- **Softr plan:** Business or Enterprise (documented).
- **Connecting needs a HubSpot Super Admin** (documented).
- **HubSpot tier, for what the integration itself reads and writes:** contacts, companies, deals,
  tasks and tickets work on HubSpot Free (documented, HubSpot's product catalog). Custom objects need
  HubSpot Enterprise (documented). HubSpot's *own* workflows need Professional or higher, and
  ticket-based workflows need Service Hub Professional or Enterprise (documented). A Softr workflow
  does not need either ([Workflows](#workflows-softr-workflows-with-hubspot)).

## Connection Setup

1. In Softr Studio, go to Data Sources and select HubSpot.
2. Authenticate via OAuth as a HubSpot Super Admin.
3. Pick the HubSpot object to connect (see [Supported objects](#supported-objects)).
4. Some HubSpot fields and objects need **Sensitive Data scopes** for API access (documented). If a
   field you expect comes back empty or missing, check those scopes first.

An object appears only if HubSpot grants Softr access to it. Reconnecting restores one that is
missing (documented).

**Through the MCP** (verified live 2026-10-05): `integration_list_databases` on a HubSpot integration
returns the object ids. For HubSpot the `databaseId`, the `tableId` and the `tableName` are all that
same object id (`tickets`, `line_items`, …), so pass the object id three times to
`integration_list_table_fields` and `vibe_coding_block_connect_data_source`.

## Supported objects

Softr's docs list **15 objects** since softr-public-documentation PR #127 (merged 2026-09-24; the
list had 7 before). The live integration returned **14 object ids**, i.e. all except Custom Objects,
which that portal did not have (verified live 2026-10-05).

**Listed does not mean usable, and usable does not mean writable.** Softr publishes no per-object
write matrix, and vibe-block writes have been tested on tickets and deals only (2026-10-05).

| Object | Id | Primary field | What to know |
|---|---|---|---|
| Contacts | `contacts` | `hs_full_name_or_email` | HubSpot Free. The natural users table. Has no `associatedcompanyid` in Softr (see [Field model](#field-model)) |
| Companies | `companies` | `name` | HubSpot Free |
| Deals | `deals` | `dealname` | HubSpot Free. Stage ids are portal-specific |
| Tickets | `tickets` | `subject` | HubSpot Free. A create needs `subject` and `hs_pipeline_stage` ([Writing](#writing)) |
| Tasks | `tasks` | `hs_task_subject` | HubSpot Free |
| Notes | `notes` | `hs_body_preview` | A create needs `hs_timestamp`. HubSpot says a note should be associated with at least one record. Links can be written on a ticket create ([Association writes](#association-writes)); a note create with links is untested |
| Leads, Listings, Appointments | `leads`, `listings`, `appointments` | — | Listed live; not examined in the 2026-10-05 run |
| Projects | `projects` | `hs_name` | **Must be activated in HubSpot by a Super Admin** (Data Management > Data Model; documented). On a portal where it apparently wasn't, Softr still listed the object, but its `hs_pipeline` / `hs_pipeline_stage` had **zero choices** (verified live). HubSpot requires both on create (documented), so no create can succeed there |
| Products | `products` | `name` | Catalog entries. Links go only to deals and to other products, none to companies or contacts |
| Line Items | `line_items` | `name` | **Need a parent object** (deal, quote, subscription, invoice or payment link; documented). No links to companies or contacts |
| Invoices | `invoices` | `hs_number` | **Need Commerce Hub** (documented). A draft needs only `hs_currency`; moving one to Open needs an associated contact and at least one line item (HubSpot API docs) |
| Subscriptions | `subscriptions` | `hs_name` | **Need Commerce Hub. Treat as read-only:** HubSpot's API needs HubSpot payments or Stripe for writes, and it cannot set associations at all (documented) |
| Custom Objects | — | — | **Need HubSpot Enterprise** (documented). Appear only when they exist in the portal |

Softr's Workflows HubSpot page says Add / Update / Delete work "across every HubSpot object". That is
a marketing line. HubSpot's own API rules above contradict it for subscriptions, and for projects
until activation. Don't quote it to a client as a write guarantee.

**Native blocks vs vibe blocks.** Softr's HubSpot page says "You can connect only one object type to
one block". That rule is for native blocks. A vibe block connects several objects with
`datasource.define` plus `from:` on every hook (see
[multi-datasource.md](multi-datasource.md)).

## Field model

*Verified live 2026-10-05 via `integration_list_table_fields` and `vibe_coding_block_get_settings`,
unless marked otherwise.*

- **`fieldReferenceKey` is `"id"`.** `q.select()` uses HubSpot internal property names (`firstname`,
  `dealstage`, `hs_pipeline_stage`). Custom properties use the internal name HubSpot gave them.
- **Associations are `LINKED_RECORD` fields named `associations.<x>`**, with
  `options.linkedTableId` set to the target object. Examples:
  - deals: `associations.company` ("Associated Company"), `associations.contact`,
    `associations.deal_to_company` ("Associated Primary Company")
  - tickets: `associations.company`, `associations.contact`, `associations.ticket_to_company`
    ("Associated Primary Company"), `associations.deal`. Tickets have 13 in all.
  - companies: `associations.company_to_deal`, `associations.company_to_ticket`,
    `associations.company_to_contact` (the "with Primary Company" links), 20 in all.

  Read them as you would any linked field: an association can arrive as a single `{ id, label }`
  object as well as an array of them, so normalise before you `.map()` (see
  [reading.md](reading.md#filtering-by-a-linked-record-server-side)). In a vibe hook (verified
  live 2026-10-05 on tickets), `associations.company` and `associations.contact` read as arrays
  of `{ id, label }`, usually with the record's name as the label (one re-read shortly after a
  link update showed the company's id instead; see [Association writes](#association-writes)).
  The primary-company link `associations.ticket_to_company` read as one `{ id, label }` object,
  or `null` (seen once, in a re-read shortly after a link update, while a company was still
  linked; HubSpot's primary label was not checked). A Softr workflow's Find record output showed
  the single-object case too.
- **SELECT fields carry id→label choices** in `options.choices`, and HubSpot ids are not labels.
  - **Deals:** stage ids are portal-specific. The live portal had `6183367908` = Initial Contact
    … `closedwon` = Closed Won, in pipeline `default` ("Sales Pipeline").
  - **Tickets:** they use `hs_pipeline_stage`, which held `1` New, `2` Waiting on contact,
    `3` Waiting on us and `4` Closed, all in pipeline `0` ("Support Pipeline"). That is a fresh
    portal's default, so read the choices from the schema rather than hardcoding them.
  - **Owners:** `hubspot_owner_id` choices are numeric HubSpot owner ids, labelled
    "Name (email)".
- **`hubspot_owner_email` and `hubspot_owner_name` are fields Softr derives, not HubSpot
  properties.** HubSpot returns them as `propertiesNotFound`, yet they appear as SELECT fields on
  every object. Filtering on them is untested, because HubSpot's search has no such property to
  filter on. Filter and write ownership through **`hubspot_owner_id`**, which is the real property.
- **Softr exposes only a subset of HubSpot's properties.** Tickets showed 36 of about 122 HubSpot
  properties, plus the 2 derived owner fields; invoices showed 26 of about 94. Missing on tickets
  are `hs_all_associated_contact_emails`, `hs_v2_date_entered_*`, `hs_resolution`, `hs_ticket_id`,
  `hs_tag_ids` and `hs_object_source_label`. Softr's docs say "All default HubSpot object
  properties" are supported; the live schema contradicts that. **Custom properties are exposed:**
  the portal's custom ticket properties (`issue_category`, `issue_severity`) were in the schema.
  Before designing around a property, confirm it is in the field list.
- **Field metadata has no read-only flag.** Each field carries only `id`, `name`, `type` and
  `options`. HubSpot-computed properties (`hs_object_id`, `createdate`, `hs_lastmodifieddate`,
  `num_associated_*`) look exactly like writable ones.
- **Contacts have no `associatedcompanyid` in Softr**, and HubSpot also returned it as not found. A
  contact reaches its company only through `associations.company` /
  `associations.contact_to_company`, or through the free-text `company` property.
- `hs_file_upload` on tickets is an ATTACHMENT in Softr but a plain string property in HubSpot.
  Writing it is untested.

## Writing

| Field kind | Writable? | Evidence |
|---|---|---|
| Default properties | Yes | **Verified live** 2026-10-05: `dealstage` and `hs_pipeline_stage` with `useRecordUpdate`, and `subject`, `content`, `hs_pipeline` and `hs_pipeline_stage` on a ticket create with `useRecordCreate`; the rest documented (Softr's HubSpot page) |
| Custom properties | Yes | Documented; untested from a vibe block |
| Softr computed fields (Calculation, Rollup, Count, Formula) | Read-only | Documented. These are the **only** fields Softr's page lists as read-only |
| HubSpot-computed properties (`hs_object_id`, `createdate`, `hs_lastmodifieddate`, `num_associated_*`) | Presumably not | Inferred from HubSpot; nothing in Softr's metadata says so |
| Associations (`associations.*`) | Yes for a ticket's company and contact links; an update replaced the company list | **Verified live** 2026-10-05 on one ticket's `associations.company` and `associations.contact` ([below](#association-writes)); other links, including the primary company, untested |
| `hubspot_owner_email` / `hubspot_owner_name` | Don't | Softr-derived; write `hubspot_owner_id` instead (inferred) |

- **Ticket create:** HubSpot requires `subject` and `hs_pipeline_stage`. `hs_pipeline` is optional
  when the portal has one ticket pipeline, because the default is used (documented, HubSpot API).
  **Note create:** `hs_timestamp` is required (documented).
- **Write a SELECT by its choice id** (verified live 2026-10-05). `fields: { stage: "closedwon" }`
  on `dealstage` and `fields: { status: "1" }` on `hs_pipeline_stage` both saved, and so did a
  ticket create with `hs_pipeline: "0"` and `hs_pipeline_stage: "1"`. The id and the
  label differ (`'1'` vs `'New'`, `'6183367908'` vs `'Initial Contact'`). Softr Database is the
  other way round: there the **label** is written
  ([writing.md](writing.md#dropdown--single-select-softr-database)). Whether HubSpot also accepts
  a label is untested.
- **What goes over the wire** (verified live 2026-10-05, ticket stage write):
  - The write is `PATCH …/blocks/<block>/datasources/<connection id>/records-trigger/<recordId>`
    with the body `{"context":{…},"fields":{"hs_pipeline_stage":"1"}}`. Fields are keyed by
    HubSpot property id, and the value is a plain string.
  - The response holds only the written field, in its read shape:
    `{"record":{"id":"…","fields":{"hs_pipeline_stage":{"id":"1","label":"New"}}},"triggerResponse":null}`.
  - The connection id in the write URL is internal: the deals connection's id changed when the
    block was recompiled. Reads use the alias (`…/datasources/tickets/records`). This only
    matters when reading a network log.
- **The write endpoint enforces visibility** (verified live 2026-10-05). A client who replayed an
  account manager's PATCH got 403. The block and its actions were both limited to account
  managers, so the test did not show which of the two rules refused it. Every code push resets
  action visibility (Hard Constraint 21 in SKILL.md), so re-lock it and read it back after each push.

### What HubSpot changes after a write

*Verified live 2026-10-05 on one test ticket and one test deal. The writes came from a vibe
block in preview; the results were read back through the HubSpot MCP and the block's own list
reads.*

- **A deal's close date is overwritten when it closes, won or lost.** Entering `closedwon` or
  `closedlost` sets `closedate` to the moment of the write: `closedwon` replaced a planned date
  four months away, and `closedlost` later did the same. Reopening the deal, or undoing the
  change, kept the new date; the old one had to be restored by hand. Say so in the confirm step
  before a block closes a deal.
- **A ticket's close date is cleared when it reopens.** Entering the closed status set
  `closed_date` and `time_to_close`. Moving the ticket back to an open status cleared both.
- **Probability and weighted amount lag behind the stage.** HubSpot recalculates
  `hs_deal_stage_probability` and `hs_projected_amount` after the write (table below).
- **HubSpot modifies a ticket again about 10 s after a stage write.** `hs_lastmodifieddate`
  moved again 9 to 11 s after each of the three stage writes where it was checked.
- **Stage writes leave associations alone.** They do leave a permanent stage history
  (`hs_v2_date_entered_*` / `hs_v2_date_exited_*`), even when the value is put back.

What the block's own list reads returned for the deal (Closed Lost, then Undo 5 s later):

| Read of `deals` | `dealstage`, `closedate` | `hs_deal_stage_probability`, `hs_projected_amount` |
|---|---|---|
| +4 s after Closed Lost | `closedlost`, the new date | 0.1 and 1,980: the values from before the write |
| +4 s after the Undo | Initial Contact, the new date kept | 0 and 0: Closed Lost's values |
| +12 s after the Undo | Initial Contact, the new date kept | 0.1 and 1,980: correct |

So the stage and the close date were readable within 4 s, while the computed fields were still
one write behind at that point. No read follows a write unless the block asks. A block that
shows any of these fields should, on top of the `refetch()` in `onSuccess`, read the table again
about 4 s and 12 s after each successful save
([pattern](writing.md#fields-the-source-changes-after-the-write)). A read right after the write
was not measured.

### Association writes

*Verified live 2026-10-05 from a test block in Studio preview, "Preview as" Softr's built-in Test
User (the builder's session acting as that user, who had no HubSpot record): one ticket, one
company and one contact. HubSpot's MCP confirmed the links, the company count and the source;
the primary-company link and the link labels were seen only in the block's own reads. Not
tested: a create with `[{ id }]` objects, objects other than tickets, writing the primary-company
link directly, and a real client login on the published app.*

To Softr's action parser the association fields are ordinary fields. With `associations.company`
and `associations.contact` in the hooks' `fields:` selects, the derived ADD_RECORD and
UPDATE_RECORD actions listed both ("Associated Company", "Associated Contact"), and both hooks
were enabled.

**Create: link with an array of id strings.** This worked:

```tsx
const ticketCreateFields = q.select({
  subject: "subject",
  pipeline: "hs_pipeline",
  stage: "hs_pipeline_stage",
  company: "associations.company",
  contact: "associations.contact",
});

// Inside the block: const createTicket = useRecordCreate({ from: ds.tickets, fields: ticketCreateFields });
await createTicket.mutateAsync({
  subject,
  pipeline: "0",          // choice ids, not labels
  stage: "1",
  company: [companyId],   // an array of id strings, as on Softr Database
  contact: [contactId],
});
```

- **The ticket was linked to the written company and contact** (confirmed in HubSpot). In Softr's
  read, the written company was also the primary company (`associations.ticket_to_company`);
  whether Softr's write set that or HubSpot did is not known.
- **An extra company link appeared.** The ticket was also linked to the contact's other company,
  which was also that contact's primary company. The block wrote only the one company, so HubSpot
  most likely added it (inferred), perhaps through a portal setting (unchecked). Whether it adds
  every company of the contact or only the primary one is open. Expect extra company links on a
  ticket created with a contact (seen once).
- **Link labels are not always names.** The create's result labelled both links with their ids
  (`{ "id": "450812074179", "label": "450812074179" }`), and the update's result did the same for
  the company. A re-read after the create had the names. A re-read about 15 s after the update
  still labelled the company with its id while the contact had its name; a later read had the
  name. When a label equals its id, take the name from the companies or contacts the block
  already reads, or show the id.
- **HubSpot records the source** as `INTEGRATION`, detail "Softr".

**Update: `[{ id }]` objects, and the update replaced the company list.**

- `useRecordUpdate` with `company` and `contact` both as `["<id>"]` failed with **500**
  (`Failed to update record: 500`) and, in the block's re-read, changed nothing, although the
  create had accepted that shape.
- `company: [{ id }]` and `contact: [{ id }]` worked, and the company list was **replaced**: the
  extra company was removed (HubSpot's company count went from 2 to 1). In the block's re-read
  about 15 s later, `associations.ticket_to_company` was `null` although the written company stayed
  linked, so expect the primary-company link to be lost (not checked in HubSpot). The contact list
  held only the written contact before and after, so whether contact links are replaced too could
  not be seen (likely; inferred).
- So, with the two shapes tried, an update could not add one link on its own: `["<id>"]` failed
  and `[{ id }]` replaced the list. A block can write the whole list back with the new id added
  (untested; it may lose the primary label, as the test's update did), or leave it to the
  workflow route below.
- An update whose `fields:` select held no association fields left the links alone: later stage
  writes on this ticket came from another block whose update select held only the stage, and the
  ticket kept its company. Whether leaving them out of the payload is enough when they are in the
  select is untested, so keep association fields out of any update select that is not meant to
  write them.

**Nothing checked the link ids.** The create linked the ticket to a company and a contact that had
nothing to do with the Test User who sent it. In this test the tickets connection had no Source
condition and the create action had no record condition. Whether a Source condition, an action's
record condition or a real client session checks the links on a create or an update is untested.
The request comes from the browser, so treat link ids as client input: a client could probably
link a new ticket to another company, and that company's portal would then show it (inferred).
For client-facing creates, set or check the links server-side with the workflow route below.

*History: this page called association writes "read-only" until 2026-10-05 (no source), then
"unverified" until the test above.*

**Workflow route (documented; not run in these tests): a Softr workflow calls HubSpot's
associations API.** Use it to add a link without replacing the list, to set the primary label, or
to set a client's links server-side.

- **The step:** a **Run custom code** step (`CUSTOM_CODE` v1.2.0) with the HubSpot integration
  attached. `fetch()` calls to `api.hubapi.com` then carry that integration's credentials, with no
  token in the code. Those credentials carry only the scopes granted when HubSpot was connected.
  A call to an object Softr's connector doesn't support yet may get HubSpot's 403 (Softr engineer,
  2026-10-07; the scope list is not published).
- **Plan and testing:** the step needs a paid Softr plan, and it is `REAL_ONLY`, so a test run
  writes for real.
- **Limits:** about 2 minutes per run, and up to 20 fetches per second.
- **The HubSpot calls** (associations v4):
  - Unlabeled: `PUT /crm/objects/2026-09/ticket/{ticketId}/associations/default/company/{companyId}`,
    and the same pattern for `contact`.
  - Labeled, e.g. primary company: `PUT /crm/objects/2026-09/ticket/{ticketId}/associations/company/{companyId}`
    with body `[{ "associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 26 }]`.
  - Type ids: ticket→contact **16**, ticket→company **339**, ticket→primary company **26**.
  - `DELETE` on the same path unlinks.
  - HubSpot's ticket-create endpoint also accepts an `associations` array, so one step can create
    the ticket already linked.
- **Starting it from the block:** call `navigate(setting, { recordId, datasourceId })` on a
  `TRIGGER_CUSTOM_WORKFLOW` setting inside `useRecordCreate`'s `onSuccess` (see SKILL.md's
  NavigationAction section). The vibe path documents only `recordId` and `datasourceId` as payload.
  The trigger is a browser-callable endpoint, so the workflow should re-read the ticket from HubSpot
  rather than trust what it receives.
- **No block wiring:** a `HUBSPOT_RECORD_CREATED` trigger on tickets plus the same custom-code step
  can link each new ticket by a requester-email property. This also catches tickets created in
  HubSpot itself. The cost is trigger latency (unknown, see below) and a run for every new ticket.
- **Why the block can't do it itself:** `useProxyFetch` is documented for REST API sources only.
  Call API authenticates only REST_API integrations and needs Professional or higher, so it would
  need a HubSpot private-app token stored as a REST integration (inferred). Any user who can call
  the proxy could then use that token for any path on HubSpot's API
  ([why](rest-api.md#the-proxy-is-not-access-control)).
- **HubSpot-side route:** a HubSpot workflow's "Create associations" action needs Pro or
  Enterprise, and ticket-based workflows need Service Hub Pro or Enterprise (documented). It
  matches records by exact, case-sensitive property value.

## Row scoping — who sees which records

A connection's **Source conditions are the only server-side row gate**. A `where` in block code is a
request parameter the caller controls, not access control. See
[../references/softr-mcp.md](../references/softr-mcp.md#what-the-server-enforces-on-a-blocks-data-endpoints)
(verified 2026-09-18 on Softr Database; on HubSpot 2026-10-05, below).

A **REST API source pointed at HubSpot** (`useProxyFetch` with a private-app token) has no row gate
at all. The proxy forwards any path on `api.hubapi.com` that the browser sends (Softr engineers,
2026-10-07); see [rest-api.md](rest-api.md#the-proxy-is-not-access-control). Serve client-facing
rows from the native connection. Objects it lacks, such as conversations and feedback submissions,
need one of the server-side routes listed there.

The **block's Visibility** is enforced on the same endpoints, all or nothing (verified 2026-10-05 on
HubSpot). A block gated to an "Account managers" condition group returned every deal and ticket to
members from connections with no Source condition, and 403 on list and by-id to clients, a
Softr-only user and logged-out visitors. So a staff view can be a group-gated block with
unfiltered connections. The same tables on an ungated block are open to anyone who may view the
page ([details](multi-datasource.md#one-connection--one-read-payload-the-union-of-its-selects)).

- **Scope clients by company with the user's own field** (verified 2026-10-05). A Source
  condition `associations.company IS_ONE_OF ["USER:::associations.company"]`, logical operator
  AND, on the deals and the tickets connections gave each client only their own companies'
  records: Dana 1 deal and 1 ticket, Tom 1 deal. The users table is the contacts table, so
  `USER:::associations.company` is the logged-in contact's own company association. The token is
  `USER:::<user field id>`, **no braces**, as the entire value. It was set in Studio's Source tab
  and over MCP alike ([details](../references/softr-mcp.md#logged-in-user-values-in-source-conditions)).
  - **It fails closed.** A synced contact with no company, a Softr-only user and account managers
    without a company all got 0 rows. By-id reads of other companies' records returned 404.
  - **So staff need their own block**, gated to their group, with unfiltered connections (above).
    Widening the client condition for them would widen it for everyone.
  - **Use AND.** With one rule OR and AND behave the same, but a second rule added under OR widens
    access.
- **The email token is different: `{USER:::EMAIL}`, with braces**, as the entire value. It is
  verified on Softr Database and untested on HubSpot. For any other user field, pick it once in the
  block's Source tab and read `dataSources[].condition` back with `vibe_coding_block_get_settings`.
- **Community evidence for association scoping in native blocks.** In
  [community.softr.io/t/hubspot-conditional-filter/10572](https://community.softr.io/t/hubspot-conditional-filter/10572)
  (September 2024), a native filter "ticket's Associated Company ID = logged-in user's Associated
  Company ID" worked after a Softr fix. It used an older field model; `associatedcompanyid` is no
  longer on Softr's contacts. Softr's HubSpot page also says "You can also use associated objects
  in Visibility Conditional Filters". The vibe-block version above is the verified one.
- **Fallback: put the user's email on the records**, for scoping that no user field can express. Add
  a custom text property, e.g. "Portal requester email" on tickets or "Account manager email" on
  companies and deals. Write it when the record is created, and compare it with `{USER:::EMAIL}`
  using **IS**. If the property holds a list of emails and you use CONTAINS, mind the substring
  trap: `bob@x.com` also matches `jbob@x.com` (verified 2026-09-18 on Softr Database). The value is
  written by the browser, so a determined user could tamper with it on create. That is acceptable
  for scoping a demo; production needs a server-side source of identity. The user's company
  association above lives in HubSpot instead, out of reach of a block with no contact write action.
  Association fields can be written like other fields ([Association writes](#association-writes),
  verified on tickets), so a contacts write action a client can reach could let them rewrite their
  own company links and widen their own scope (inferred; contact association writes untested).
  Keep `associations.company` out of any such action.
- **Writes are a separate question.** Whether a Source condition limits what a create or an
  update may write, such as the link ids on a new ticket, is untested. A create on a connection
  without one, run in preview, accepted links to a company and a contact unrelated to the user
  ([Association writes](#association-writes)).
- **Owner scoping.** `hubspot_owner_id` is the real property, but on a contact it names that
  contact's owner, not the contact. Scoping "my deals" for an account manager would need a custom
  contact property holding their own owner id, read through `USER:::<field id>` (untested). For a
  team-wide staff view, a group-gated block with unfiltered connections needs no owner filter at
  all. Owners are also HubSpot users, i.e. HubSpot seats.

**Filter limits** ([docs.softr.io/troubleshooting/troubleshooting-hubspot-errors](https://docs.softr.io/troubleshooting/troubleshooting-hubspot-errors)):

- **Softr's numbers:** 5 groups × 6 filters, 18 filters per block in total, and only **4 AND
  filters on a block with an Edit button**.
- **What counts:** conditional filters, inline search and filter, and action-visibility filters
  (documented). A code `where` presumably lands in the same HubSpot search request (inferred).
- **AND and OR are swapped on Softr's page.** It calls the groups "AND" and the filters inside them
  "OR". HubSpot's search API is the other way round: filters inside a group are ANDed and groups are
  ORed, with the same 5 / 6 / 18 caps (documented).
- **HubSpot search also caps:** a query returns at most 10,000 results (documented). Associations
  are filtered through the `associations.{objectType}` pseudo-property, which does not cover
  custom-object associations (documented).
- **The MCP's record-filter tool** takes one flat AND/OR list per connection, and each value is an
  array of strings. ARRAY fields allow `IS`, `IS_ONE_OF`, `IS_NONE_OF`, `HAS_ALL_OF`, `IS_EMPTY` and
  `IS_NOT_EMPTY`, with no `CONTAINS` (verified 2026-10-05 from the tool's description).

## Rate limits

- **110 requests per 10 seconds per HubSpot account** for apps distributed through the HubSpot
  Marketplace. The search API is counted separately, and HubSpot's API-limit add-on does not raise
  this (documented). That Softr's connection counts as such an app is **inferred**: Softr has a
  Marketplace listing.
- **The CRM search API allows 5 requests per second per account** (documented). How Softr turns
  hook calls into HubSpot calls is not documented. If list reads go through search, several
  HubSpot connections on one page, times concurrent users, can reach that limit (inferred).
- **New and updated records take "a few moments" to appear in search results** (documented). A
  `refetch()` right after a mutation may therefore still return the old value (inferred, not
  measured). A list read at +4 s had the written stage, while HubSpot's computed fields were
  still stale at +4 s and correct by +12 s (verified live 2026-10-05,
  [details](#what-hubspot-changes-after-a-write)). Show the written value optimistically and
  read again later.
- Softr also caches data-source reads ("short-term" on one docs page, "24 hour" on another; scope
  unspecified). See [overview.md](overview.md).

## User sync

- **HubSpot supports 2-way user sync** (documented). Email is required and is the unique
  identifier. Name, Magic link, Avatar, Created date and Last seen date map too. All other contact
  properties remain usable in user groups, conditional filters and `useCurrentUser({ properties })`.
- **Filtered sync** ("Selected", with rules) is available (documented; listed under Business on
  Softr's pricing page).
- **Deleting a Softr user deletes the HubSpot contact.** Deleting in HubSpot does not delete the
  Softr user (documented). The filtered-sync option "Delete their user account" also removes the
  data-source record (documented).
- **`createUserInDatasource` defaults to `true`** on `application_create_user_connection`, so users
  added in Softr create HubSpot contacts. To keep people out of HubSpot (e.g. internal account
  managers), use the "Let the user only exist in the Softr app" option (documented).
- **Sync is continuous only on a published app.** In Studio, or on an unpublished app, it runs on
  login, on publish and when the Users tab is opened (documented).
- **Even on a published app the lag varies** (verified 2026-10-05). A new HubSpot contact appeared
  as a Softr user after 33 s in the morning; two more, created later that day, took 24 min. Never
  assume real time: confirm the user exists with `application_list_users` before testing as them.
- **An app has one users table** (documented). Account managers are therefore either contacts in the
  same table or Softr-only users.
- **`useCurrentUser().id` exists only when user sync is on** (documented). Whether it equals the
  HubSpot contact id is **unverified**.
- **User Caching** (App Settings > Advanced) keeps the **logged-in user's own record** for 2 minutes.
  Softr recommends leaving it on, and suggests turning it off when user-group membership updates
  slowly (documented). It affects group membership and logged-in-user values, not how fresh other
  records are. A ticket-status lag comes from elsewhere: the search delay above, data-source
  caching, or workflow trigger latency.
- **Condition-based user groups on a synced HubSpot property work** (verified 2026-10-05). For a
  select contact property the rule is subject `USER:portal_role` (the property's internal name),
  type `ARRAY`, operator `IS_ONE_OF`, value `[<choice id>]`: the choice id, not the label. That
  syntax is for **user groups**. In a block's Source condition the subject form returned 400; there
  the user field goes in the value, as `USER:::<field id>` (see above). Membership then lives in
  HubSpot: anyone who can edit that property there can grant the group's access.
- **`application_list_users` is not a membership check.** It showed `userGroups: []` for every
  user, including members of condition groups that demonstrably applied (verified 2026-10-05).
  Test membership by what the user can reach, e.g. preview as them against a group-gated block, or
  read their groups in the preview
  ([how](../references/softr-mcp.md#testing-as-any-app-user-without-logins--the-preview-as-switcher);
  same result on Softr Database, 2026-10-07).

## Audit trail

- **HubSpot records a connected app's writes with change source "Integration"**, not the person who
  made the edit. Only edits made in HubSpot's own UI show a user's name and email (documented). A
  2022 HubSpot developer changelog adds that the app's ID is recorded.
- **Integration writes cannot be restored with one click.** Property history offers Restore only for
  CRM UI edits, imports and workflows (documented).
- What HubSpot puts in "Updated by user ID" for a Softr write is **unknown**. Records written by a
  different connector carried an ID that belonged to no user in the portal (verified live; not a
  Softr write).
- **Workaround:** write a "Last edited in Softr by" custom property from `useCurrentUser().email`
  on every create and update. The value is self-reported, because the browser sends it. That is fine
  for a trail, but it is not security.
- Emails sent by a Softr workflow's Send email step don't appear on the HubSpot record's timeline.
  Logging them as a note would need an association write (inferred).

## Workflows (Softr Workflows with HubSpot)

*Catalog and specs verified live 2026-10-05.*

- **Triggers: `HUBSPOT_RECORD_CREATED` and `HUBSPOT_RECORD_UPDATED`** (v1.0.0, both `REAL_ONLY`).
  - Their only inputs are `integrationId`, `type` (the object id, e.g. `"tickets"`) and an optional
    `objectTypeId`.
  - There is **no property filter**. Softr Tables and Airtable "record updated" triggers have an
    `updateField` option; these don't.
  - Whether a data-source integration connected before triggers existed can run them is untested.
    Zoho's docs say to reconnect in that case.
- **Latency is unknown.**
  - Neither trigger appears on Softr's Trigger Types page, and the HubSpot Workflows page lists
    actions only.
  - The Trigger Types page says only Softr Tables, Calendly, Attio and Zoho CRM are instant and
    "other services use background polling". That sentence is wrong for Stripe (Softr registers a
    webhook) and for DocuSign (pushed by Docusign Connect), so it can't be relied on for HubSpot
    either.
  - Time a real run before promising anything.
- **Record updated fires on any change to any record of that object.** Expect it to fire on
  HubSpot's internal recalculations and on Softr's own writes too (inferred). HubSpot does modify
  a record again about 10 s after a stage write (measured on a ticket, 2026-10-05), so one stage
  change from a block may fire it twice (inferred; the trigger was not run). Build two things in
  from the start:
  - **A stage filter.** Note that a filter on the *current* stage alone fires again on every later
    edit to a ticket already in that stage.
  - **A dedupe property**, e.g. `softr_last_notified_stage`: filter on `stage != it`, and set it
    after acting. Softr exposes no `hs_v2_date_entered_*` property to tell a stage entry apart from
    other edits.
- **Actions:** Add record (`MOCK_AND_REAL`), Update record (`REAL_ONLY`), Update multiple records,
  Delete record, Delete multiple records, Find record and Find multiple records.
  - **There is no associate action.**
  - Add and Update take a `fields` input of type `DATA_SOURCE_FIELDS`. Whether `associations.*`
    is offered there, or actually written, is unknown.
- **Find record output** is `{ id, fields }`. Associations arrive as lists of `{ id, label }`
  (e.g. `fields["associations.contact"][*].id`), though some single-label associations come back
  as one `{ id, label }` object. SELECT fields arrive as `{ id, label }`, so compare on `.id`. This
  was seen on a companies sample from a mock test; the same shape on tickets is inferred.
- Workflow nodes call the workspace's HubSpot integration directly, with `type` set to the object
  id, so an object need not be connected to any block for a workflow to use it.

## Gotchas

- **Listed is not usable.** Projects needs activation, Subscriptions are read-only, Invoices and
  Subscriptions need Commerce Hub, Line Items need a parent, Custom Objects need HubSpot Enterprise.
- **Association links: create with `["<id>"]`, update with `[{ id }]`, and an update replaced the
  ticket's whole company list** (verified live 2026-10-05, one ticket); Softr then read no primary
  company (not checked in HubSpot). A ticket created with a contact may also get another of that
  contact's companies. Treat link ids as client input.
- **SELECT ids ≠ labels, and writes take the id** (verified live 2026-10-05; label untested).
  Take display labels from the schema's choices (`useFieldOptions` should serve them, but that
  is untested on HubSpot); don't hardcode stage ids across portals.
- **Closing a deal overwrites its close date, and reopening keeps the new one.** Reopening a
  ticket clears its close date. See [What HubSpot changes after a write](#what-hubspot-changes-after-a-write).
- **After a save, read again at about 4 s and 12 s** on top of the usual `refetch()`. No read
  follows a write on its own, and HubSpot's computed fields arrive late.
- **The owner email and name fields are Softr's, not HubSpot's.** Filter and write
  `hubspot_owner_id`.
- **Only part of each object's properties is exposed.** Check a property is in the field list
  before relying on it.
- **Mind the filter budget on blocks with an Edit button:** 4 AND filters, counting Source
  conditions, inline search and action-visibility filters together.
- **Scope client rows with `USER:::associations.company`, no braces,** in a Source condition
  joined by AND. It fails closed, so give staff their own group-gated block.

## Best For

- Client and partner portals on top of HubSpot-managed contacts and companies
- Support ticket portals
- Sales portals and deal rooms
- CRM dashboards for teams or clients
- Any app where HubSpot is the system of record
