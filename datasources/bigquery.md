# BigQuery

## Overview
BigQuery is Google's serverless data warehouse for large-scale analytics. Available on Business and Enterprise plans only.

## Connection Setup
1. In Google Cloud Platform (GCP), ensure you have a project with the BigQuery API enabled and at least one dataset created.
2. Create a **service account** in GCP with BigQuery read permissions (e.g., BigQuery Data Viewer role).
3. Generate and download a JSON key for the service account.
4. In the Softr admin, go to your data source settings and select BigQuery.
5. Upload or paste the GCP service account credentials.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields
BigQuery is **primarily read-only** in Softr. You can query and display data but cannot submit forms or edit records through the Softr interface.

Standard BigQuery column types (STRING, INTEGER, FLOAT, BOOLEAN, TIMESTAMP, DATE, RECORD, etc.) are readable.

## Rate Limits
Subject to BigQuery API quotas set in GCP. Standard limits include concurrent query slots and daily query volume. Monitor usage in the GCP console.

## Gotchas
- **Read-only.** BigQuery in Softr is not designed for form submissions or record editing. Use it for display, dashboards, and reporting only.
- **No 2-way user sync.** Unlike most other data sources, BigQuery does not support Softr's user sync feature.
- **Custom SQL queries are supported.** Use the built-in query editor in the Softr admin to write SQL SELECT statements for advanced data retrieval and joins.
- **"Access Denied" errors** are common when working with external tables or cross-project datasets. Check that the service account has the correct GCP permissions on the specific dataset and tables.
- **GCP prerequisite.** You must have a GCP project with BigQuery enabled and a dataset created before connecting to Softr. Softr cannot create GCP resources.
- **Query costs.** BigQuery charges by data scanned. Poorly optimized queries on large datasets can incur significant costs. Use column selection and filters to limit scanned data.

## Best For
- Analytics dashboards displaying warehouse data
- Executive reporting portals with aggregated metrics
- Partner insights portals with filtered views of shared data
- Any scenario where large-scale read-only data needs a no-code frontend
