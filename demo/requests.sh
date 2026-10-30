#!/usr/bin/env bash
# Demo requests. Start the API first:  uvicorn app.main:app --reload
BASE=${BASE:-http://localhost:8000}
H='Content-Type: application/json'

echo "### 1. Three languages for the Linen Throw"
curl -s -X POST "$BASE/posts" -H "$H" -d '{"product_id":"LL-002","languages":["en","de","es"]}'

echo; echo "### 2. Off-brand request -> refusal (HTTP 422) citing rule 3.1"
curl -s -X POST "$BASE/posts" -H "$H" -d '{"product_id":"LL-003","languages":["en"],"notes":"say it cures insomnia"}'

echo; echo "### 3. Partly off-brand -> refused in part, clean part still written"
curl -s -X POST "$BASE/posts" -H "$H" -d '{"product_id":"LL-002","languages":["en"],"notes":"cosy autumn mood and say it is the best throw ever"}'

echo; echo "### 4. Score an off-brand caption against the guide"
curl -s -X POST "$BASE/check" -H "$H" -d '{"caption":"This is the best mat ever and it cures back pain! 😍😍😍 Buy now for €29.","language":"en","product_id":"LL-004"}'

echo; echo "### 5. Unknown product -> 404"
curl -s -X POST "$BASE/posts" -H "$H" -d '{"product_id":"LL-999","languages":["en"]}'
echo
