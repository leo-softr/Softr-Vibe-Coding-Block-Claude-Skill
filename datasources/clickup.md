# ClickUp

## Overview
ClickUp is a project and task management platform. Available on Professional plans and above.

## Connection Setup
1. In the Softr admin, go to your data source settings and select ClickUp.
2. Authenticate via OAuth -- you will be redirected to ClickUp to authorize your workspace.
3. Navigate to the desired Space > Folder > List. Each block connects to one List at a time.

## Vibe Coding Field IDs
Use the Field Inspector block to determine exact field IDs for this data source.

## Supported Fields

**Writable fields:**

| Field Type     | Notes |
|----------------|-------|
| Number         | |
| Text           | |
| Long Text      | |
| Dropdown       | |
| Date           | |
| Money          | |
| Website        | |
| Rating         | |
| Status         | ClickUp-native status field |
| Priority       | ClickUp-native priority field |
| Checkbox       | |
| Relationship   | Linked tasks |
| Email          | |
| Phone          | |
| Label          | |
| Short Text     | |

**Read-only fields:**

| Field Type           | Notes |
|----------------------|-------|
| Formula              | |
| People               | |
| Tasks                | |
| Voting               | |
| Users                | |
| Date Created         | Auto-set by ClickUp |
| Date Updated         | Auto-set by ClickUp |
| Assignees            | |
| Signature            | |
| Files                | |
| Automatic Progress   | |
| Location             | |

**Not supported:**

| Field Type | Reason |
|------------|--------|
| Rollup     | Not exposed by the ClickUp API |

## Rate Limits
Rate limits vary by ClickUp plan:

| ClickUp Plan   | Limit          |
|----------------|----------------|
| Free / Business | 100 req/min   |
| Business Plus  | 1,000 req/min  |
| Enterprise     | 10,000 req/min |

For Free/Business plans, paginate aggressively and avoid loading large datasets on page load.

## Gotchas
- **One List per block.** Each Softr block connects to a single ClickUp List. To display data from multiple Lists, use separate blocks.
- **Sub-tasks are not natively supported** in the block connection. Sub-tasks will not appear unless they exist as top-level tasks in the connected List.
- **Multi-list tasks** are supported -- a task that belongs to multiple Lists can appear when any of those Lists is connected.
- **Rollup fields are not available** because the ClickUp API does not expose them.
- **Low-tier rate limits** (100 req/min on Free/Business) can cause issues with high-traffic pages. Consider caching strategies or upgrading the ClickUp plan.

## Best For
- Client portals showing project/task status
- Status dashboards for team visibility
- Internal team apps built around ClickUp workflows
- Task management interfaces with rich field support
