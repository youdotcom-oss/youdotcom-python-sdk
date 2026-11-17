export async function requestReview({ env = process.env, fetchImpl = fetch } = {}) {
  const serviceUrl = env.INPUT_SERVICE_URL?.replace(/\/$/, "");
  const pullNumber = Number(env.INPUT_PR_NUMBER);
  const commentId = env.INPUT_COMMENT_ID ? Number(env.INPUT_COMMENT_ID) : undefined;
  if (!serviceUrl?.startsWith("https://")) throw new Error("service_url must be an https URL");
  if (!Number.isInteger(pullNumber) || pullNumber < 1) throw new Error("pr_number must be a positive integer");
  if (commentId !== undefined && !Number.isInteger(commentId)) throw new Error("comment_id must be an integer");
  if (!env.ACTIONS_ID_TOKEN_REQUEST_URL || !env.ACTIONS_ID_TOKEN_REQUEST_TOKEN) throw new Error("OIDC is unavailable; grant the job id-token: write");
  const tokenUrl = new URL(env.ACTIONS_ID_TOKEN_REQUEST_URL);
  tokenUrl.searchParams.set("audience", serviceUrl);
  const tokenResponse = await fetchImpl(tokenUrl, { headers: { authorization: `bearer ${env.ACTIONS_ID_TOKEN_REQUEST_TOKEN}` } });
  if (!tokenResponse.ok) throw new Error(`OIDC token request failed (${tokenResponse.status})`);
  const { value } = await tokenResponse.json();
  const response = await fetchImpl(`${serviceUrl}/workflow/review`, {
    method: "POST",
    headers: { authorization: `Bearer ${value}`, "content-type": "application/json" },
    body: JSON.stringify({ pull_number: pullNumber, ...(commentId !== undefined ? { comment_id: commentId } : {}) }),
  });
  const result = await response.json().catch(() => ({}));
  if (response.status === 200 && result.ignored === true) return result;
  if (response.status !== 202) throw new Error(`YouCode Review rejected the request (${response.status}${result.error ? `: ${result.error}` : ""})`);
  return result;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  requestReview().then((result) => console.log(result.ignored ? "Not a review request; nothing to do." : result.duplicate ? "Review already requested." : "Review requested."), (error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}
