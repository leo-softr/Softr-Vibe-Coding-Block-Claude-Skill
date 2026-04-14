# SQL Database

## Overview
Direct connection to an external SQL database (PostgreSQL, MySQL, SQL Server, or MariaDB). Available on Business and Enterprise plans only.

## Connection Setup
1. Ensure your database server is accessible from the internet (or via a static IP).
2. **Whitelist Softr IP addresses** in your database firewall:
   - `3.120.79.212`
   - `3.123.159.186`
   - `52.58.246.121`
3. In the Softr admin, go to your data source settings and select SQL Database.
4. Enter the connection credentials:
   - Host
   - Port (defaults: PostgreSQL `5432`, MySQL/MariaDB `3306`, SQL Server `1433`)
   - Database Name
   - User
   - Password
5. Select the database type (PostgreSQL, MySQL, SQL Server, or MariaDB).

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields
Field support depends on the underlying database engine. Standard column types for each engine are writable. Generated columns, computed columns, and views are read-only.

| Engine        | Common Writable Types |
|---------------|----------------------|
| PostgreSQL    | text, integer, boolean, timestamp, jsonb, uuid, numeric, varchar |
| MySQL/MariaDB | varchar, int, tinyint, datetime, text, decimal, json, enum |
| SQL Server    | nvarchar, int, bit, datetime2, decimal, uniqueidentifier |

## Rate Limits
No Softr-imposed rate limits. Performance depends on your database server's capacity and connection limits. Unlimited records and unlimited concurrent users from Softr's side.

## Gotchas
- **IP whitelisting is required.** Connections will be refused if the three Softr IPs are not allowed through your firewall.
- **Custom SQL SELECT queries are supported.** Use the built-in query editor in the Softr admin for advanced retrieval, joins across tables, and filtered views.
- **Database-level access control applies.** The database user you provide determines what tables and operations are available. Use a scoped user with minimal required permissions.
- **Default ports matter.** If your database runs on a non-standard port, specify it explicitly in the connection settings.
- **Connection pooling is managed by Softr.** You do not need to configure a connection pool, but ensure your database allows enough concurrent connections for your expected traffic.
- **No ORM or migration support.** Softr connects to your existing schema. Table creation and schema changes must be done directly in your database.

## Best For
- Companies with existing SQL databases that want a no-code frontend
- Enterprise apps requiring high security with database-level access control
- Projects needing complex queries with joins across multiple tables
- Teams that manage their own infrastructure and want full control over the data layer
