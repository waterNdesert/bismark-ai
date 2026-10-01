import { expect, test, type Page } from "@playwright/test";

const user = {
  id: "10000000-0000-0000-0000-000000000001",
  email: "reader@example.test",
  aud: "authenticated",
  role: "authenticated",
  app_metadata: { provider: "email", providers: ["email"] },
  user_metadata: {},
  created_at: "2026-01-01T00:00:00Z",
};
const token = "test-access-token";
const session = {
  access_token: token,
  refresh_token: "test-refresh",
  token_type: "bearer",
  expires_in: 3600,
  user,
};
const organizationId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const workspaceId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const workspaceId2 = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
const apiUrl = "http://127.0.0.1:8100";
const endpoint = `${apiUrl}/api/v1/organizations/${organizationId}/workspaces/${workspaceId}/documents`;
const uploadedDocument = {
  id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  organization_id: organizationId,
  workspace_id: workspaceId,
  original_filename: "handbook.txt",
  mime_type: "text/plain",
  size_bytes: 12,
  status: "uploaded",
  created_at: "2026-10-01T12:00:00Z",
};

type Role = "owner" | "admin" | "member";
type WorkspaceRole = "admin" | "member";

function context(
  role: Role,
  workspaceIds: string[] = [workspaceId],
  workspaceRole: WorkspaceRole = "member",
) {
  return {
    organizations: [
      {
        id: organizationId,
        name: "Bismark Development",
        role,
        workspaces: workspaceIds.map((id, index) => ({
          id,
          name: `Workspace ${index + 1}`,
          role: workspaceRole,
        })),
      },
    ],
  };
}

async function login(
  page: Page,
  role: Role,
  workspaceIds?: string[],
  workspaceRole?: WorkspaceRole,
) {
  await page.route("https://auth.example.test/auth/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/logout")) return route.fulfill({ status: 204 });
    if (path.endsWith("/user")) return route.fulfill({ json: user });
    return route.fulfill({ json: session });
  });
  await page.route(`${apiUrl}/api/v1/me`, (route) =>
    route.fulfill({
      json: { id: user.id, email: user.email, display_name: null },
    }),
  );
  await page.route(`${apiUrl}/api/v1/me/context`, async (route) => {
    expect(route.request().headers().authorization).toBe(`Bearer ${token}`);
    await route.fulfill({ json: context(role, workspaceIds, workspaceRole) });
  });
  await page.goto("/");
  await page.getByLabel("Email address").fill(user.email);
  await page.getByLabel(/^Password/).fill("test-only-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.locator(".desktop-sidebar")).toBeVisible();
}

async function openUpload(
  page: Page,
  route = "/app/sources",
  label = "Add files",
) {
  await page.goto(route);
  await page.getByRole("button", { name: label, exact: true }).click();
  await expect(
    page.getByRole("dialog", { name: "Manual Upload" }),
  ).toBeVisible();
}

test("owner can upload with selected tenant, bearer token, and multipart file", async ({
  page,
}) => {
  await login(page, "owner");
  let requestCount = 0;
  await page.route(endpoint, async (route) => {
    requestCount += 1;
    const request = route.request();
    expect(request.method()).toBe("POST");
    expect(request.headers().authorization).toBe(`Bearer ${token}`);
    expect(request.headers()["content-type"]).toMatch(
      /^multipart\/form-data; boundary=/,
    );
    expect(request.postData()).toContain(
      'name="file"; filename="handbook.txt"',
    );
    await route.fulfill({ status: 201, json: uploadedDocument });
  });
  await openUpload(page);
  await page.getByLabel("Choose a file", { exact: true }).setInputFiles({
    name: "handbook.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("hello world!"),
  });
  await expect(page.getByText("handbook.txt", { exact: true })).toBeVisible();
  await expect(page.getByText(/12 bytes/)).toBeVisible();
  await page.getByRole("button", { name: "Upload to workspace" }).click();
  await expect(page.getByRole("status")).toContainText("uploaded");
  await expect(page.getByText("Processed")).toHaveCount(0);
  await expect(page.getByText("Indexed")).toHaveCount(0);
  await expect(page.getByText("handbook.txt", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/storage_path|source_id|service.role/i),
  ).toHaveCount(0);
  await expect(
    page.getByRole("link", { name: "Go to Documents" }),
  ).toBeVisible();
  expect(requestCount).toBe(1);
});

test("admin can access upload on Sources and Documents reuses the same flow", async ({
  page,
}) => {
  await login(page, "admin");
  await page.goto("/app/sources");
  await expect(page.getByRole("button", { name: "Add files" })).toBeEnabled();
  await openUpload(page, "/app/documents", "Upload document");
  await expect(
    page.getByRole("heading", { name: "Document library" }),
  ).toBeVisible();
});

test("member cannot reach upload flow", async ({ page }) => {
  await login(page, "member");
  await page.goto("/app/sources");
  await expect(page).toHaveURL(/\/app\/ask$/);
  await expect(page.getByRole("button", { name: "Add files" })).toHaveCount(0);
});

test("selected file can be removed and replaced", async ({ page }) => {
  await login(page, "owner");
  await openUpload(page);
  const picker = page.getByLabel("Choose a file", { exact: true });
  await picker.setInputFiles({
    name: "first.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("a"),
  });
  await expect(page.getByText("first.txt", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Remove selected file" }).click();
  await expect(page.getByText("first.txt", { exact: true })).toHaveCount(0);
  await picker.setInputFiles({
    name: "second.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("second"),
  });
  await expect(page.getByText("second.txt", { exact: true })).toBeVisible();
});

test("upload is unavailable until a workspace is selected", async ({
  page,
}) => {
  await login(page, "owner", [workspaceId, workspaceId2]);
  await page.goto("/app/sources");
  await expect(page.getByRole("combobox", { name: "Workspace" })).toHaveValue(
    "",
  );
  await expect(page.getByRole("button", { name: "Add files" })).toBeDisabled();
});

test("workspace admin with organization member role cannot upload", async ({
  page,
}) => {
  await login(page, "member", [workspaceId], "admin");
  await page.goto("/app/sources");
  await expect(page).toHaveURL(/\/app\/ask$/);
});

test("documents page keeps truthful empty state and does not fabricate a list", async ({
  page,
}) => {
  await login(page, "owner");
  await page.goto("/app/documents");
  await expect(
    page.getByRole("heading", { name: "Document library" }),
  ).toBeVisible();
  await expect(page.getByText("Listing coming soon")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Upload document" }),
  ).toBeEnabled();
});

const failures = [
  [400, "", /couldn’t accept this file/i],
  [401, "", /sign in again/i],
  [403, "", /don’t have permission/i],
  [409, "SOURCE_UNAVAILABLE", /upload source is unavailable/i],
  [500, "", /try again/i],
] as const;
for (const [status, code, message] of failures) {
  test(`upload maps ${status}${code ? ` ${code}` : ""} to a safe message`, async ({
    page,
  }) => {
    await login(page, "owner");
    await page.route(endpoint, (route) =>
      route.fulfill({
        status,
        json: {
          error: { code: code || "INTERNAL", message: "raw internal detail" },
        },
      }),
    );
    await openUpload(page);
    await page.getByLabel("Choose a file", { exact: true }).setInputFiles({
      name: "handbook.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("data"),
    });
    await page.getByRole("button", { name: "Upload to workspace" }).click();
    await expect(
      page.getByRole("dialog", { name: "Manual Upload" }).getByRole("alert"),
    ).toContainText(message);
    await expect(page.getByText("raw internal detail")).toHaveCount(0);
  });
}

test("network failure displays safe retry state", async ({ page }) => {
  await login(page, "owner");
  await page.route(endpoint, (route) => route.abort());
  await openUpload(page);
  await page.getByLabel("Choose a file", { exact: true }).setInputFiles({
    name: "handbook.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("data"),
  });
  await page.getByRole("button", { name: "Upload to workspace" }).click();
  await expect(
    page.getByRole("dialog", { name: "Manual Upload" }).getByRole("alert"),
  ).toContainText("try again");
});

test("duplicate submit sends only one request", async ({ page }) => {
  await login(page, "owner");
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  let requests = 0;
  await page.route(endpoint, async (route) => {
    requests += 1;
    await pending;
    await route.fulfill({ status: 201, json: uploadedDocument });
  });
  await openUpload(page);
  await page.getByLabel("Choose a file", { exact: true }).setInputFiles({
    name: "handbook.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("data"),
  });
  const submit = page
    .getByRole("dialog", { name: "Manual Upload" })
    .locator(".upload-actions .app-button");
  await submit.click();
  await expect(submit).toBeDisabled();
  release();
  await expect(page.getByRole("status")).toContainText("uploaded");
  expect(requests).toBe(1);
});

test("coming-soon sources remain noninteractive", async ({ page }) => {
  await login(page, "owner");
  await page.goto("/app/sources");
  for (const connector of [
    "Website",
    "Google Drive",
    "Notion",
    "SharePoint",
    "Dropbox",
  ]) {
    await expect(
      page.getByRole("heading", { name: connector, exact: true }),
    ).toBeVisible();
    const connectorCard = page
      .locator(".connector-card")
      .filter({
        has: page.getByRole("heading", { name: connector, exact: true }),
      });
    await expect(connectorCard.getByRole("link")).toHaveCount(0);
    await expect(connectorCard.getByRole("button")).toHaveCount(0);
  }
});
