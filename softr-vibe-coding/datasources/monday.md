# monday.com

## Overview
Project management platform used as a data source for Softr. Requires a Professional plan or higher in Softr. Connects via API token.

## Connection Setup
1. In monday.com, go to Administration > API > Personal API Token and copy the token.
2. In Softr admin, go to Data Sources and select monday.com.
3. Paste the API token to authenticate.
4. Select the monday.com board and group to connect.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for your monday.com board columns. Column names or internal IDs assigned by monday.com are used as field identifiers.

## Supported Fields

| Field Type           | Writable  | Notes |
|----------------------|-----------|-------|
| Text                 | Yes       | |
| Number               | Yes       | |
| Date                 | Yes       | |
| Status               | Yes       | |
| Dropdown             | Yes       | |
| Checkbox             | Yes       | |
| Email                | Yes       | |
| Phone                | Yes       | |
| Link                 | Yes       | |
| People               | Yes       | |
| File                 | Yes       | |
| Connected Boards     | Limited   | Linked records between boards are supported |
| Mirror               | Read-only | Reflects data from connected boards |
| Created By           | Read-only | |
| Created At           | Read-only | |
| Last Updated         | Read-only | |
| Item ID              | Read-only | |

## Rate Limits
monday.com enforces API rate limits based on your monday.com plan tier. Softr requests count against your monday.com API quota. Recommended maximum: **50-100 concurrent users**. Beyond that, API throttling may cause slow or failed requests.

## Gotchas
- **Professional+ Softr plan required.** monday.com is not available on Free or Basic Softr plans.
- **API token authentication only.** Uses a Personal API Token from monday.com's admin settings, not OAuth.
- **Connected Boards** (linked records between boards) are supported but may have limitations depending on the board configuration.
- **Mirror columns are read-only.** These reflect data from connected boards and cannot be written to from Softr.
- **Status columns** use monday.com's internal label/index system. Map these appropriately in your block logic for display purposes.
- **Subitems** may require additional configuration to surface correctly in Softr blocks.

## Best For
- Client-facing project portals without giving clients direct monday.com access
- Status dashboards for stakeholders
- Task management interfaces for external collaborators
- Teams using monday.com as their project management backbone
