# API Integration Template (Beginner-Friendly)

Use this for every API you connect to WRAITH.

---

## 1) API Summary

- API name:
- Provider URL:
- Why we need it:
- Is it required or optional:

## 2) Authentication

- Auth type (API key / OAuth / JWT / none):
- Where credentials are stored (`.env`, secret manager):
- Required env vars:
  - `API_KEY=`
  - `API_BASE_URL=`

## 3) Endpoint Map

| Purpose | Method | Endpoint | Required Params |
|---------|--------|----------|-----------------|
| | | | |

## 4) Rate Limits + Retry Rules

- Published rate limit:
- Retry strategy (exponential backoff, max retries):
- Timeout settings:

## 5) Example Request

```bash
curl -X GET "https://api.example.com/v1/resource?query=test" \
  -H "Authorization: Bearer <TOKEN>"
```

## 6) Example Response

```json
{
  "status": "ok",
  "data": []
}
```

## 7) Error Handling Plan

| HTTP/Code | Meaning | User-facing message | Action |
|-----------|---------|---------------------|--------|
| 400 | bad request | Check query format | validate inputs |
| 401 | unauthorized | API credentials invalid | rotate/update key |
| 429 | rate limit | API busy, retrying | backoff + retry |
| 500 | server error | Provider issue | retry + fallback |

## 8) Security Notes

- Do not commit secrets.
- Use `.env` locally and secure secrets in deployment.
- Log minimal sensitive data.

## 9) QA Checklist

- [ ] Success path tested
- [ ] Invalid auth tested
- [ ] Rate-limit response tested
- [ ] Timeout behavior tested
- [ ] Error messages understandable to beginner user
