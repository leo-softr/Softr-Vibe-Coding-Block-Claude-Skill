# Xano

## Overview
Xano is a no-code backend-as-a-service (BaaS) built on PostgreSQL. Available on Professional plans and above.

## Connection Setup
1. In your Xano workspace, enable the **Database Connector** add-on.
2. Note the public IP address and credentials (Host, User, Password) from the Database Connector settings.
3. In the Softr admin, go to your data source settings and select Xano.
4. Enter the credentials: Host, User, and Password.
5. Use **Full Access** credentials (recommended) for read/write, or **Read-Only** for display-only apps.
6. **Whitelist Softr IP addresses** in your Xano firewall settings:
   - `3.120.79.212`
   - `3.123.159.186`
   - `52.58.246.121`
7. Once connected, all workspaces and tables in that Xano instance are available.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields
Field support follows PostgreSQL column types since Softr connects via direct database access. Standard column types (text, integer, boolean, timestamp, etc.) are writable. Computed/generated columns are read-only.

## Rate Limits
No Softr-imposed rate limits. Xano handles concurrency at the database level. Unlimited records and unlimited concurrent users.

## Gotchas
- **Direct database access, not API.** Softr connects to Xano's PostgreSQL database directly via the Database Connector. It does NOT go through Xano's custom API endpoints. Business logic in Xano API stacks will not execute on Softr reads/writes.
- **Database Connector must be enabled.** This is a separate add-on in Xano -- the connection will fail without it.
- **IP whitelisting is required.** If you skip whitelisting the three Softr IPs, connections will be refused.
- **Full Access vs Read-Only credentials** determine whether Softr can write data. Choose based on your use case.

## Best For
- Scalable applications with complex backend logic in Xano
- Apps that need unlimited records and concurrent users
- Projects where Xano handles business logic via API stacks and Softr provides the frontend
- Teams wanting a dedicated backend with PostgreSQL power and a no-code UI layer
