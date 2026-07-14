const BACKEND_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

export async function GET(request: Request) {
  const cookie = request.headers.get("cookie");
  const backendResponse = await fetch(`${BACKEND_URL}/api/v1/admin/auth/me`, {
    headers: cookie ? { Cookie: cookie } : {},
  });

  const data = await backendResponse.json();
  return Response.json(data, { status: backendResponse.status });
}
