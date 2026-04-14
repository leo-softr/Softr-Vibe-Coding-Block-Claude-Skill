# Coda

## Overview
Document, table, and automation platform used as a data source for Softr. Requires a Basic plan or higher in Softr. Connects via API token (not OAuth).

## Connection Setup
1. In Coda, go to Account Settings > API Settings and generate an API token.
2. In Softr admin, go to Data Sources and select Coda.
3. Paste the API token to authenticate.
4. Select the Coda document and table to connect.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for your Coda tables. Column names in Coda are typically used as field identifiers.

## Supported Fields

| Field Type           | Writable  | Notes |
|----------------------|-----------|-------|
| Text                 | Yes       | |
| Number               | Yes       | |
| Date                 | Yes       | |
| Select List          | Yes       | |
| Attachment           | Yes       | Large attachments may slow block rendering |
| Checkbox             | Yes       | |
| URL                  | Yes       | |
| Email                | Yes       | |
| People               | Limited   | Depends on Coda's API exposure |
| Formula              | Read-only | |
| Button               | Read-only | Not actionable in Softr |

## Rate Limits
Coda enforces its own API rate limits based on your Coda plan. Softr requests count against your Coda API quota. Suitable for moderate traffic. Refer to Coda's API documentation for current limits on your plan.

## Gotchas
- **API token authentication only.** Coda does not use OAuth for Softr. The token is generated manually in Coda's account settings.
- **Embedded Coda docs are not supported** in Vibe Coding blocks. You cannot render a full Coda document inside a Softr block; only table data is accessible.
- **Advanced Coda automations** (buttons, automations, Packs) do not execute through Softr. Only raw table data is read and written.
- **Large attachments** stored in Coda may cause slow rendering in Softr blocks. Optimize file sizes where possible.
- **Coda formulas** are read-only. Calculated columns cannot be written to from Softr.

## Best For
- Teams using Coda for internal workflows who want an external-facing portal
- Building portals without requiring Coda seat licenses for every end user
- Projects where Coda's table and automation features are already in use as the backend
