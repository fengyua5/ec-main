const BACKEND_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.json();
  const backendResponse = await fetch(`${BACKEND_URL}/api/v1/admin/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await backendResponse.json();
  const response = new Response(JSON.stringify(data), {
    status: backendResponse.status,
    headers: { "Content-Type": "application/json" },
  });

  for (const c of backendResponse.headers.getSetCookie()) {
    response.headers.append("Set-Cookie", c);
  }

  return response;
}
