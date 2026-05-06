# Data Source Overview

## Comparison Matrix

| Data Source | Max Records | Concurrent Users | Security | Skill Level | Vibe Coding Approach |
|---|---|---|---|---|---|
| Softr Databases | 1M+ | Unlimited | Medium | Low | `useRecords` + `q.select()` |
| Airtable | 500K | 200-300 | Medium | Low | `useRecords` + `q.select()` |
| Google Sheets | 1M+ | 50-100 | Low | Low | `useRecords` + `q.select()` |
| SmartSuite | 500K | 200-300 | Medium | Low | `useRecords` + `q.select()` |
| HubSpot | 1M+ | 500-1000 | Medium | Medium | `useRecords` + `q.select()` |
| monday.com | 500K | 50-100 | Low | Low | `useRecords` + `q.select()` |
| Xano | Unlimited | Unlimited | High | High | `useRecords` + `q.select()` |
| SQL Database | Unlimited | Unlimited | High | High | `useRecords` + `q.select()` |
| Supabase | Unlimited | Unlimited | High | High | `useRecords` + `q.select()` |
| Notion | 1M+ | 50-100 | Medium | Low | `useRecords` + `q.select()` |
| ClickUp | 500K | 50-100 | Medium | Low | `useRecords` + `q.select()` |
| Coda | 1M+ | 200-300 | Medium | Low | `useRecords` + `q.select()` |
| BigQuery | Unlimited | N/A | Low | Medium | `useRecords` + `q.select()` |
| REST API | Unlimited | N/A | Varies | High | `useProxyFetch` + `useQuery` |

## Selection Guide

- **New projects with no existing data** -> Softr Databases (no rate limits, native performance, included in subscription)
- **Existing spreadsheet data** -> Airtable or Google Sheets (easy migration, one-click import from Airtable)
- **Scalable backend with full API control** -> Xano, Supabase, or SQL
- **Any data source not natively supported** -> REST API

## Key Concepts

- Softr does **not store or sync** external data -- it proxies requests in real-time (with 24-hour caching).
- Data is connected to **dynamic blocks** (List, Grid, Table, Kanban, Chart, Form, etc.) in the Softr Studio.
- **Multiple data sources** can coexist in a single Softr app, even on the same page.
- Softr IP addresses to whitelist for secured databases: `3.120.79.212`, `3.123.159.186`, `52.58.246.121`

## User Sync Availability

| Source | 2-Way User Sync |
|---|---|
| Softr Databases, Airtable, Google Sheets, HubSpot, Notion, Coda, monday.com, SmartSuite, ClickUp, Xano, Supabase, SQL Database | Supported |
| BigQuery, REST API | Not supported |
