# REST API Data Source

## Overview

A generic connector that allows Softr to connect to virtually any external platform or service that exposes an HTTP REST API. This is the escape hatch for any source not natively supported.

**Plan requirement:** Business and Enterprise Softr plans only.

**Authentication:** Any header-based auth (API keys, Bearer tokens, Basic Auth, etc.) configured manually.

**2-way user sync:** Not supported.

**Best for:** Connecting any external service with an API; extending Softr's native integrations; building RevOps or automation workflows where Softr serves as a frontend for tools like Salesforce, Pipedrive, Stripe, Luma, or custom internal APIs.

## Connection Setup

### Step 1: Add REST API as a data source
Data Sources > Connect Data Source > Choose **REST API**. Select a pre-built template (Stripe, Salesforce, Pipedrive, Asana, Shopify, etc.) or **Add Manually**.

### Step 2: Set up default headers
These headers apply to all endpoints in the connection:
- **Name**: A label to identify the REST API connection.
- **Headers**: Key-value pairs for universal headers (e.g., `Authorization: Bearer YOUR_TOKEN`, custom header for API key, etc.).

### Step 3: Add API Resources (Endpoints)
Each resource is a specific API endpoint. Supports **GET** and **POST** methods.

For each resource:
- **Name**: A label for the endpoint.
- **HTTP Method**: GET (fetch data) or POST (create records).
- **URL**: The endpoint URL from the API's documentation.
- **Headers tab**: Endpoint-specific headers (in addition to default headers).
- **URL Params tab**: Query string parameters. Can use placeholders (see below).
- **Body tab**: JSON body for POST requests.
- **Pagination tab**: Configure cursor or offset-based pagination parameters.
- **Transformer tab**: Vanilla JavaScript to reshape the API's JSON response.

Click **Execute** to test the endpoint before saving.

### Step 4: Schema setup
After a successful test call:
- **Key**: The field name from the JSON response.
- **Type**: TEXT, NUMBER, BOOLEAN, DATE, DATETIME, TIMESTAMP, OBJECT, ARRAY, EMAIL, URL.
- **Enabled**: Toggle to show/hide the field in Softr Studio.
- **ID Field**: Mark the unique record identifier.

### Placeholders (dynamic values)
- `{LOGGED_IN_USER: <FIELD>}` -- inject logged-in user data (e.g., `{LOGGED_IN_USER: StripeID}`)
- `{recordId}` -- inject the currently selected record ID
- `{filter.<FIELD>}` -- pass filter/search values from Softr block filters into the API request

Placeholders can be used anywhere: headers, URL, URL params, body.

### Transformer Example
For APIs with nested responses (e.g., Luma's `entries[].event` structure):

```javascript
return data.entries.map(function(entry) { return entry.event; });
```

## Vibe Coding Integration

**REST API data sources use a completely different pattern from Airtable/Softr Database.** They use `useProxyFetch` + `useQuery` instead of `useRecords` + `q.select()`.

### useProxyFetch + useQuery

```jsx
import { useProxyFetch } from "@/lib/datasource";
import { useQuery } from "@tanstack/react-query";

export default function Block() {
  var proxyFetch = useProxyFetch();

  var result = useQuery({
    queryKey: ["my-data"],
    queryFn: function() {
      return proxyFetch("https://api.example.com/v1/data")
        .then(function(res) {
          if (!res.ok) throw new Error("Failed to fetch data");
          return res.json();
        });
    },
  });

  var data = result.data;
  var status = result.status;   // "pending" | "success" | "error"
  var error = result.error;

  if (status === "pending") { /* loading UI */ }
  if (status === "error") { /* error UI */ }

  // Access the raw API response directly -- no record.fields nesting
  var items = (data && data.entries) || [];
}
```

### How It Works

- `useProxyFetch` returns a fetch function that routes requests through Softr's proxy
- Softr injects the authentication headers configured in the data source automatically
- API keys are **never exposed** in client-side code
- The response is the raw API JSON -- access fields directly (e.g., `item.name`, not `record.fields.name`)

### Dynamic Query Parameters

Build URLs with dynamic values. Include them in the `queryKey` so React Query refetches when they change:

```jsx
var proxyFetch = useProxyFetch();
var afterDate = new Date().toISOString();

var result = useQuery({
  queryKey: ["events", afterDate],
  queryFn: function() {
    var url = "https://api.example.com/v1/events?after=" + encodeURIComponent(afterDate);
    return proxyFetch(url)
      .then(function(res) {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      });
  },
});
```

### POST Requests

`proxyFetch` accepts the same options as standard `fetch`:

```jsx
var result = useQuery({
  queryKey: ["search", searchTerm],
  queryFn: function() {
    return proxyFetch("https://api.example.com/v1/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: searchTerm }),
    })
      .then(function(res) {
        if (!res.ok) throw new Error("Search failed");
        return res.json();
      });
  },
  enabled: searchTerm.length > 0,
});
```

### Sending Webhooks (Non-Proxy)

For outbound requests to services that don't need proxy auth (e.g., Softr workflow webhooks), use regular `fetch()`:

```jsx
fetch("https://workflows-api.softr.io/v1/workflows/WORKFLOW_ID/executions/EXECUTION_ID", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ data: { key: "value" } }),
});
```

### Key Differences from useRecords

| | useRecords (Airtable/Softr DB) | useProxyFetch (REST API) |
|---|---|---|
| Field mapping | `q.select()` with aliases | None -- raw API response |
| Data access | `record.fields.alias` | Direct (e.g., `item.name`) |
| Response shape | `data.pages[].items[]` | Whatever the API returns |
| Pagination | Built-in `fetchNextPage` | Manual via URL params + cursor |
| Filtering | `q.text()`, `q.number()`, etc. | API query params or client-side |
| Auth | Handled by Softr | Proxied through Softr (key hidden) |
| Mutations | `useRecordCreate/Update/Delete` | Direct `fetch()` or `proxyFetch()` |

## Limitations

- Supports GET and POST methods only in the data source connector (no PUT, PATCH, DELETE -- use Softr Action buttons with custom API call actions for those)
- Response data must be parseable JSON
- No 2-way user sync
- Requires Business or Enterprise plan

## Debug Utility

Use this block to inspect the raw API response:

```jsx
import { useProxyFetch } from "@/lib/datasource";
import { useQuery } from "@tanstack/react-query";
export default function Block() {
  var proxyFetch = useProxyFetch();
  var result = useQuery({
    queryKey: ["api-inspect"],
    queryFn: function() {
      return proxyFetch("YOUR_FULL_API_URL_HERE")
        .then(function(res) { return res.json(); });
    },
  });
  if (result.status === "pending") return <div className="container py-6"><div className="content"><p>Loading...</p></div></div>;
  if (result.status === "error") return <div className="container py-6"><div className="content"><p className="text-red-500">Error: {result.error && result.error.message}</p></div></div>;
  return (
    <div className="container py-6">
      <div className="content">
        <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", wordBreak: "break-all", background: "#f9fafb", padding: 16, borderRadius: 8 }}>
          {JSON.stringify(result.data, null, 2)}
        </pre>
      </div>
    </div>
  );
}
```
