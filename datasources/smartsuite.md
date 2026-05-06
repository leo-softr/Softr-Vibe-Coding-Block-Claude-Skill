# SmartSuite

## Overview
SmartSuite is a work management and relational database platform. Available on Professional plans and above.

## Connection Setup
1. In the Softr admin, go to your data source settings and select SmartSuite.
2. Authenticate via OAuth -- you will be redirected to SmartSuite to authorize access.
3. Choose your Workspace, then select a Solution, then select a Table to connect.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields

| Field Type     | Writable | Notes |
|----------------|----------|-------|
| Text           | Yes      | |
| Number         | Yes      | |
| Date           | Yes      | |
| Dropdown       | Yes      | |
| Checkbox       | Yes      | |
| Linked Record  | Yes      | Linked records between SmartSuite tables are supported |
| Formula        | Read-only | |
| Rollup         | Read-only | |
| Lookup         | Read-only | |

## Rate Limits
Subject to SmartSuite API rate limits. Implement pagination and caching where possible to reduce request volume.

## Gotchas
- **Linked records** work across SmartSuite tables but require that both tables are within the same Solution.
- **Formula, Rollup, and Lookup fields** are read-only. Attempting to write to them will fail silently or error.
- **OAuth tokens** may expire. If data stops loading, re-authenticate via the Softr admin.

## Best For
- Teams already using SmartSuite as their primary work OS
- Apps that need relational data across multiple SmartSuite tables
- Organizations consolidating project management and app building on SmartSuite
