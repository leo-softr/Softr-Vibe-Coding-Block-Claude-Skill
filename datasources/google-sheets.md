# Google Sheets

## Overview
Cloud spreadsheet used as a simple data source for Softr. Requires a Basic plan or higher in Softr. Connects via Google OAuth.

## Connection Setup
1. In Softr admin, go to Data Sources and select Google Sheets.
2. Authenticate with your Google account via OAuth.
3. Select the spreadsheet and sheet (tab) to connect.
4. Ensure the first row contains column headers. Softr uses these as field names.
5. Softr will automatically add a "Softr Record ID" column to the sheet.

## Vibe Coding Field IDs
q.select() uses the column header names from the first row of the sheet. Use the Field Inspector block to confirm exact field IDs if headers have been renamed or modified.

## Supported Fields
Google Sheets has no native field typing. All data is text. Softr interprets values based on formatting conventions:

| Data Type      | How to Format in the Sheet | Notes |
|----------------|----------------------------|-------|
| Text           | Plain text                 | |
| Number         | Numeric value              | |
| Date           | English date formats only  | Wide range of patterns accepted (e.g., MM/DD/YYYY, YYYY-MM-DD, Month DD, YYYY) |
| Image          | URL to the image           | Must be a direct image URL |
| Multiple Images| Comma-separated URLs       | Each URL on its own, separated by commas |
| Checkbox       | `"true"` or `"false"`      | String values, not native booleans |
| Tags           | Comma-separated values     | e.g., `"Design, Marketing, Sales"` |
| Rating         | Integer 1-5                | |

## Rate Limits
Google Sheets is not designed for high-concurrency database use. Recommended maximum: **50-100 concurrent users**. Beyond that, expect slow responses and potential errors from Google's API quotas.

## Gotchas
- **No native field types.** Everything is a string. You must format data exactly as Softr expects (see table above).
- **Softr adds a "Softr Record ID" column** automatically. Do not delete or modify this column.
- **First row must be headers.** Data starts from the second row. Empty or merged header cells cause issues.
- **Date formats must be in English.** Localized date formats (e.g., DD.MM.YYYY in German locale) may not parse correctly.
- **Checkbox values are strings.** Use `"true"` and `"false"`, not `TRUE` / `FALSE` (the Google Sheets boolean formula values).
- **Low security classification.** Google Sheets lacks row-level permissions. Any user with sheet access can see all data. Not suitable for sensitive data without additional access controls in Softr.
- **Images require direct URLs.** Google Drive sharing links do not work as image sources unless converted to direct download URLs.

## Best For
- Simple apps with straightforward data
- Teams already using Google Workspace
- Low-traffic internal portals (under 50-100 concurrent users)
- Quick prototypes where setup speed matters more than performance
