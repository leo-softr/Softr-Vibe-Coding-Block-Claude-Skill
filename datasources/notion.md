# Notion

## Overview
Document and database platform used as a data source for Softr. Requires a Basic plan or higher in Softr. Connects via OAuth.

## Connection Setup
1. In Softr admin, go to Data Sources and select Notion.
2. Authenticate via OAuth with your Notion account.
3. Select the Notion database to connect.
4. If a database does not appear in the list: open Notion, click the ellipsis menu (...) on the database page, go to Connections, find Softr, and click Allow.
5. Multiple Notion workspaces can be connected to a single Softr app.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for Notion database properties. Property names in Notion are typically used as field IDs.

## Supported Fields

| Field Type           | Writable  | Notes |
|----------------------|-----------|-------|
| Title                | Yes       | |
| Text (Rich Text)     | Yes       | |
| Number               | Yes       | |
| Select               | Yes       | |
| Multi-select         | Yes       | |
| Date                 | Yes       | |
| Checkbox             | Yes       | |
| URL                  | Yes       | |
| Email                | Yes       | |
| Phone                | Yes       | |
| Files & Media        | Yes       | |
| Relation             | Limited   | Cannot be displayed in List blocks. Use Rollup workaround (see Gotchas). |
| Rollup               | Read-only | |
| Formula              | Read-only | |
| People               | Read-only | |
| Last Edited Time     | Read-only | |
| Last Edited By       | Read-only | |
| Created Time         | Read-only | |
| Created By           | Read-only | |
| ID (auto-increment)  | Read-only | |
| Button               | Read-only | |

## Rate Limits
Notion enforces its own API rate limits. Softr requests count against your Notion API quota. Performance is generally adequate for moderate traffic but is not suited for very high concurrency.

## Gotchas
- **Only database pages work.** Regular Notion pages (without a database) cannot be used as a Softr data source. The page must contain or be a Notion database.
- **Missing database in connection list:** The Notion database must explicitly grant access to the Softr integration. In Notion: ellipsis (...) > Connections > Softr > Allow.
- **Relation properties cannot be displayed in List blocks.** Workaround: create a Rollup property in Notion that pulls the desired field from the related database, then display the Rollup instead.
- **Sub-items support:** Use conditional filters to separate parent and child items. Filter by "Parent item is empty" for top-level items, "Parent item is not empty" for sub-items.
- **Formula date timezone quirk:** Formula properties that return dates may display one day off due to UTC handling differences between Notion and Softr. Test date formulas carefully.
- **Multiple workspaces:** You can connect databases from different Notion workspaces to the same Softr app.

## Best For
- Teams using Notion for project management or knowledge bases
- Internal tools and dashboards backed by Notion databases
- Content management portals where Notion is the editorial system
