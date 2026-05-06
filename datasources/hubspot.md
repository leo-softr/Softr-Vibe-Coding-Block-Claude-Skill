# HubSpot

## Overview
CRM platform used as a data source for Softr. Requires a Business or Enterprise plan in Softr. Connects via OAuth.

## Connection Setup
1. In Softr admin, go to Data Sources and select HubSpot.
2. Authenticate via OAuth with your HubSpot account.
3. Select the HubSpot object type to connect (Contacts, Companies, Deals, etc.).
4. If accessing sensitive fields, ensure Sensitive Data Scopes are enabled in your HubSpot app settings.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for HubSpot properties. Default HubSpot properties use their internal API names (e.g., `"firstname"`, `"dealstage"`, `"company"`). Custom properties use the internal name assigned by HubSpot when created.

## Supported Fields

**Supported HubSpot Objects:**
- Contacts
- Companies
- Deals
- Tickets
- Notes
- Tasks
- Custom Objects

| Field Type           | Writable  | Notes |
|----------------------|-----------|-------|
| Default Properties   | Yes       | All standard HubSpot properties for the connected object |
| Custom Properties    | Yes       | Custom properties created in HubSpot |
| Associations         | Read-only | Relational data between objects. Displayed via Linked List Blocks in Softr. |
| Calculation          | Read-only | |
| Rollup               | Read-only | |
| Count                | Read-only | |
| Formula              | Read-only | |

## Rate Limits
HubSpot enforces its own API rate limits based on your HubSpot plan tier. Softr requests count against your HubSpot API quota. Refer to HubSpot's documentation for current limits on your plan.

## Gotchas
- **Business or Enterprise Softr plan required.** HubSpot is not available on Free or Basic plans.
- **Sensitive Data Scopes** must be explicitly enabled in HubSpot for certain fields (e.g., email content, certain contact properties). Without this, those fields return empty.
- **Associations are read-only** in Vibe Coding blocks. Use Linked List Blocks to display related records (e.g., Deals associated with a Contact).
- **Custom Objects** require that the object is properly configured in HubSpot with the necessary scopes granted during OAuth.
- **Deal stages and pipeline data** use internal IDs, not display labels. Map these in your block logic if you need human-readable values.

## Best For
- Sales portals and deal rooms
- CRM dashboards for teams or clients
- Support ticket portals
- Partner portals with HubSpot-managed contacts
- Any app where HubSpot is the system of record
