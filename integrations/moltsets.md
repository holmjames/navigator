# MoltSets

Verified business email with a risk grade, carrier-verified mobile, people and company search, reverse lookups. API-first, MCP-native, flat plans. Verified against `https://developer.moltsets.com` and `https://moltsets.com/pricing/` on 2026-09-28. **Closed beta.**

## Endpoints

- REST base: `https://api.moltsets.com/api/v1/tools`
- Auth: `Authorization: Bearer ms_...`
- **Every request must carry a `User-Agent` header** (any non-empty value); without it the API returns `403 forbidden`.
- MCP: documented at `developer.moltsets.com/integrations/moltsets-mcp` (URL to confirm when the key arrives).

## Tools Navigator uses

| Endpoint | Used for | Notes |
|---|---|---|
| `POST /search_people` | Find committee members at private accounts by `title` (list OK), `company_domain`, `seniority`, `department`; suppress with `exclude_company_domain` | `title` matches the title field and is far more precise than `query`. `limit` max 25, paginate with `offset`. A miss is HTTP 200 with `status: "not_found"` and costs no tokens (but counts as a request). Fair Use windows: records per 5h and per week in `metadata.fair_use`. |
| Verified business email (with risk score) | The email in the waterfall, before Apollo | Returns `business_email`, `business_email_risk_score` (A to F), `business_email_validated_at`. Navigator uses A and B only for sends; C is verified again before use; D and below are not used. |
| Carrier-verified mobile | Mobile for the Nooks list, only when `calls_allowed` for the country | Consumes mobile tokens: 150 included on Business, $0.20 each after. |
| Email validation | Re-verify before a send when `email_validated_at` is older than 60 days | |
| Reverse email lookup | Resolve an inbound reply from an unknown address to a person | Reply flow only |

Never called: the personal-email endpoints (`docs/decisions.md` #15).

## Response shape (search_people, trimmed)

```json
{"results":{"results":[{"full_name":"...","title":"...","seniority":"Director","country":"United States",
  "linkedin_url":"https://linkedin.com/in/...","business_email":"...","business_email_risk_score":"A",
  "business_email_validated_at":"2026-08-25","current_role_start_date":"2025-10-01",
  "company":{"name":"...","domain":"...","size":"101","naics_codes":["5112"]}}],"total":278},
 "status":"ok","metadata":{"fair_use":{"records_remaining_5h":89999,"records_remaining_1w":300423}}}
```

Errors: `401` bad key; `402` out of tokens (`insufficient_tokens`, `insufficient_phone_tokens`; batch calls return partial results); `403` missing User-Agent, plan restriction, inactive account; `422` invalid input; `429` rate or Fair Use window with `Retry-After`; `500` never charged.

## Pricing (2026-09-28)

| Plan | Monthly | Requests per 5h | Mobile tokens |
|---|---|---|---|
| Starter | $27 | 5k | 10 |
| Professional | $97 | 75k | 50 |
| Business | $397 | 750k | 150 |
| Enterprise | $997 | 1.125M | 250 |

Unlimited enrichment records within the plan; extra mobile tokens $0.20. Navigator budgets Business, with mobiles at 25% of contacts.

## From Clay

HTTP API enrichment column per contact row: `POST .../search_people` or the email endpoint with `company_domain` and name, headers `Authorization` (Clay secret store) and `User-Agent: Navigator/1.0`. Suppression passed as `exclude_company_domain` from the Snowflake-fed exclude column.

## Risk

Closed beta; keys by application. Apollo is behind it on every row (`docs/pilot.md`, no-new-vendors path).

## To verify

- [ ] The MCP server URL and tool names.
- [ ] Whether a DPA is available for the enterprise tier.
- [ ] Coverage on a 200-account sample of the private book (email hit rate by grade).
