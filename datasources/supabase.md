# Supabase

## Overview
Supabase is an open-source Firebase alternative built on PostgreSQL. Available on Professional plans and above.

## Connection Setup
1. In your Supabase project, go to **Project Settings > Database**.
2. Copy the **Session Pooler** connection credentials:
   - Host
   - Database name
   - Port: `5432`
   - User
   - Password
3. **Set the Pool Size to 45 or higher** in Supabase Project Settings > Database. This is required for stable Softr connections.
4. In the Softr admin, go to your data source settings and select Supabase.
5. Enter the Session Pooler credentials.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields
Field support follows PostgreSQL column types. Standard column types (text, integer, boolean, timestamp, jsonb, uuid, etc.) are writable. Generated/computed columns are read-only.

## Rate Limits
No Softr-imposed rate limits. Supabase handles concurrency at the database and connection-pool level. Unlimited records and unlimited concurrent users.

## Gotchas
- **Pool Size must be 45+.** If the Supabase connection pool is too small, Softr connections will be dropped under load. Set this in Supabase Project Settings > Database before connecting.
- **Use Session Pooler credentials**, not the direct connection string. The Session Pooler is required for connection stability with Softr.
- **Row Level Security (RLS) applies at the database level.** Supabase RLS policies are enforced on all queries Softr makes. If records are missing, check your RLS policies.
- **Layer Softr visibility rules on top of RLS.** Softr's user-group visibility settings work independently of Supabase RLS. Use both for defense-in-depth access control.
- **Port is always 5432.** Do not use the Supabase API port (typically 443) -- Softr connects via PostgreSQL protocol.

## Best For
- Developer teams comfortable with PostgreSQL
- Applications with real-time data requirements
- Projects needing fine-grained Row Level Security
- Teams wanting an open-source backend with strong community support
