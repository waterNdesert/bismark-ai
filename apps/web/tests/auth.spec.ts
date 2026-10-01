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
const payload = {
  sub: user.id,
  exp: Math.floor(Date.now() / 1000) + 3600,
  aud: "authenticated",
  role: "authenticated",
  iss: "https://auth.example.test/auth/v1",
};
const token = `${Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url")}.${Buffer.from(JSON.stringify(payload)).toString("base64url")}.test-signature`;
const session = {
  access_token: token,
  refresh_token: "test-refresh",
  token_type: "bearer",
  expires_in: 3600,
  user,
};

async function mockServices(
  page: Page,
  rejectLogin = false,
  rejectProfile = false,
  organizations = [tenantOrganization("Alpha", 1)],
) {
  await page.route("https://auth.example.test/auth/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/logout")) return route.fulfill({ status: 204 });
    if (path.endsWith("/signup")) return route.fulfill({ json: user });
    if (path.endsWith("/recover")) return route.fulfill({ json: {} });
    if (path.endsWith("/user")) return route.fulfill({ json: user });
    if (rejectLogin)
      return route.fulfill({
        status: 400,
        json: { error_code: "invalid_credentials", msg: "Invalid credentials" },
      });
    return route.fulfill({ json: session });
  });
  await page.route("http://127.0.0.1:8100/api/v1/me/context", async (route) => {
    expect(route.request().headers()["authorization"]).toBe(`Bearer ${token}`);
    return route.fulfill({ json: { organizations } });
  });
  await page.route("http://127.0.0.1:8100/api/v1/me", async (route) => {
    expect(route.request().headers()["authorization"]).toBe(`Bearer ${token}`);
    return route.fulfill(
      rejectProfile
        ? { status: 401, json: { error: { code: "TOKEN_INVALID" } } }
        : { json: { id: user.id, email: user.email, display_name: null } },
    );
  });
}

async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Email address").fill(user.email);
  await page.getByLabel(/^Password/).fill("not-a-real-password");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
}

test("login, persisted session, and logout", async ({ page }) => {
  await mockServices(page);
  await login(page);
  await expect(page.getByText(user.email, { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(user.email, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Account menu", exact: true }).click();
  await page.getByRole("menuitem", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await expect(page.getByText(user.email, { exact: true })).toHaveCount(0);
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeVisible();
});

test("invalid login displays a safe error and enables retry", async ({
  page,
}) => {
  await mockServices(page, true);
  await login(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "Sign-in failed",
  );
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeEnabled();
  await mockServices(page);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByText(user.email, { exact: true })).toBeVisible();
});

test("API rejection never displays a verified account", async ({ page }) => {
  await mockServices(page, false, true);
  await login(page);
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "session has expired",
  );
  await expect(page.getByText(user.email, { exact: true })).toHaveCount(0);
});

test("signup requires confirmation when no session is returned", async ({
  page,
}) => {
  await mockServices(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Email address").fill(user.email);
  await page.getByLabel(/^Password/).fill("not-a-real-password");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Check your email");
  await expect(
    page.getByRole("heading", { name: "Your account", exact: true }),
  ).toHaveCount(0);
});

test("password reset request does not reveal account existence", async ({
  page,
}) => {
  await mockServices(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Forgot password?" }).click();
  await page.getByLabel("Email address").fill(user.email);
  await page.getByRole("button", { name: "Send reset link" }).click();
  await expect(page.getByRole("status")).toContainText("If an account matches");
});

test("recovery link allows changing the password and clears URL tokens", async ({
  page,
}) => {
  await mockServices(page);
  await page.goto(
    `/#access_token=${token}&refresh_token=test-refresh&expires_in=3600&token_type=bearer&type=recovery`,
  );
  await expect(
    page.getByRole("heading", { name: "Choose a new password" }),
  ).toBeVisible();
  await expect(page).toHaveURL(/^http:\/\/127\.0\.0\.1:3100\/#?$/);
  await page.getByLabel(/^New password/).fill("another-test-password");
  const update = page.waitForRequest(
    (request) =>
      request.url().endsWith("/auth/v1/user") && request.method() === "PUT",
  );
  await page.getByRole("button", { name: "Save new password" }).click();
  expect((await update).postDataJSON()).toMatchObject({
    password: "another-test-password",
  });
  await expect(page.getByRole("status")).toContainText(
    "password has been updated",
  );
});

test("mobile form fits viewport and has keyboard focus", async ({ page }) => {
  await mockServices(page);
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/");
  await expect(page.getByLabel("Email address")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Email address")).toBeFocused();
  await page.screenshot({
    path: test.info().outputPath("account-mobile.png"),
    fullPage: true,
  });
});

test("expired stored session refreshes before requesting the profile", async ({
  page,
}) => {
  await mockServices(page);
  await page.addInitScript(
    (storedSession) => {
      localStorage.setItem("sb-auth-auth-token", JSON.stringify(storedSession));
    },
    { ...session, expires_at: Math.floor(Date.now() / 1000) - 60 },
  );
  const refresh = page.waitForRequest((request) =>
    request.url().includes("grant_type=refresh_token"),
  );
  await page.goto("/");
  await refresh;
  await expect(page.getByText(user.email, { exact: true })).toBeVisible();
});

test("missing profile is initialized without sending a user ID", async ({
  page,
}) => {
  await mockServices(page);
  let initialized = false;
  await page.route("http://127.0.0.1:8100/api/v1/me", async (route) => {
    if (route.request().method() === "GET")
      return route.fulfill({
        status: 404,
        json: { error: { code: "PROFILE_NOT_FOUND" } },
      });
    expect(route.request().method()).toBe("POST");
    expect(route.request().postData()).toBeNull();
    initialized = true;
    return route.fulfill({
      json: { id: user.id, email: user.email, display_name: null },
    });
  });
  await login(page);
  await expect(page.getByText(user.email, { exact: true })).toBeVisible();
  expect(initialized).toBe(true);
});

for (const width of [1440, 1280, 768, 390]) {
  test(`app routes, navigation and account at ${width}px`, async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width, height: 900 });
    await mockServices(page);
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    await login(page);
    await expect(page).toHaveURL(/\/app$/);
    for (const route of [
      "/app",
      "/app/ask",
      "/app/sources",
      "/app/documents",
      "/app/conversations",
      "/app/members",
      "/app/analytics",
      "/app/usage",
      "/app/settings",
      "/app/account",
    ]) {
      await page.goto(route);
      await expect(page.locator("#app-content h1")).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      if (width < 1024)
        await page.getByRole("button", { name: "Open navigation" }).click();
      const navigation = page.getByRole("navigation", {
        name: "Main",
        exact: true,
      });
      if (route !== "/app/account")
        await expect(
          navigation.locator('[aria-current="page"]'),
        ).toHaveAttribute("href", route);
      if (width < 1024) await page.keyboard.press("Escape");
      await page.screenshot({
        path: test
          .info()
          .outputPath(`${route.replaceAll("/", "-")}-${width}.png`),
        fullPage: true,
      });
    }
    if (width < 1024)
      await page.getByRole("button", { name: "Open navigation" }).click();
    await page.getByRole("button", { name: "Account menu" }).click();
    await expect(page.getByRole("menuitem", { name: "Account" })).toBeFocused();
    await page.keyboard.press("ArrowDown");
    await expect(
      page.getByRole("menuitem", { name: "Sign out", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL("/");
    await page.reload();
    await expect(
      page.getByRole("heading", { name: "Welcome back" }),
    ).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("unauthenticated app routes redirect without rendering the shell", async ({
  page,
}) => {
  await mockServices(page);
  for (const route of ["/app", "/app/ask", "/app/sources", "/app/settings"]) {
    await page.goto(route);
    await expect(page).toHaveURL("/");
    await expect(
      page.getByRole("heading", { name: "Welcome back" }),
    ).toBeVisible();
    await expect(page.locator(".app-shell")).toHaveCount(0);
  }
});

test("prompt drafts, upload explanation and mobile focus behave truthfully", async ({
  page,
}) => {
  await mockServices(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  await expect(page).toHaveURL(/\/app$/);
  await page.goto("/app/ask");
  await page
    .getByRole("button", { name: "Summarize a policy for my team" })
    .click();
  await expect(page.getByLabel("Ask a question", { exact: true })).toHaveValue(
    "Summarize a policy for my team",
  );
  await expect(
    page.getByRole("button", { name: "Send question — coming soon" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("dialog", { name: "Navigation" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Open navigation" }),
  ).toBeFocused();
  await page.goto("/app/documents");
  await page.getByRole("button", { name: "Upload document" }).click();
  await expect(
    page.getByRole("dialog", { name: "Manual Upload" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Drop a file here or choose a file" }),
  ).toBeEnabled();
  await expect(
    page.getByRole("button", { name: "Upload to workspace" }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Upload document" }),
  ).toBeFocused();
});

test("logout clears the local session even if the provider is unavailable", async ({
  page,
}) => {
  await mockServices(page);
  await login(page);
  await expect(page).toHaveURL(/\/app$/);
  await page.route("https://auth.example.test/auth/v1/logout*", (route) =>
    route.fulfill({ status: 500, json: { message: "Unavailable" } }),
  );
  await page.getByRole("button", { name: "Account menu" }).click();
  await page.getByRole("menuitem", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL("/");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
});

test("Ask composer grows, keeps drafts local, and respects keyboard input", async ({
  page,
}) => {
  await mockServices(page);
  await login(page);
  await expect(page).toHaveURL(/\/app$/);
  await page.goto("/app/ask");
  const input = page.getByLabel("Ask a question", { exact: true });
  await expect(input).toBeVisible();
  const requests: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/chat")) requests.push(request.url());
  });
  const initial = await input.evaluate((element) => element.clientHeight);
  await input.fill("A question");
  await input.press("Enter");
  await expect(input).toHaveValue("A question");
  await input.press("Shift+Enter");
  await expect(input).toHaveValue("A question\n");
  await input.fill(
    Array.from({ length: 30 }, (_, index) => `Draft line ${index}`).join("\n"),
  );
  await expect
    .poll(() => input.evaluate((element) => element.clientHeight))
    .toBeGreaterThan(initial);
  expect(
    await input.evaluate((element) => element.clientHeight),
  ).toBeLessThanOrEqual(200);
  expect(
    await input.evaluate(
      (element) => element.scrollHeight > element.clientHeight,
    ),
  ).toBe(true);
  await input.fill("");
  await expect
    .poll(() => input.evaluate((element) => element.clientHeight))
    .toBe(initial);
  await page
    .getByRole("button", { name: "Explain this using company sources" })
    .click();
  await expect(input).toBeFocused();
  await expect(input).toHaveValue("Explain this using company sources");
  await expect(
    page.getByRole("button", { name: "Send question — coming soon" }),
  ).toBeDisabled();
  await expect(page.getByRole("article")).toHaveCount(0);
  await expect(
    page.getByText("Draft only. Nothing is sent or saved.", { exact: false }),
  ).toBeVisible();
  expect(requests).toEqual([]);
});

function tenantOrganization(
  name: string,
  count: number,
  role: "owner" | "admin" | "member" = "admin",
  workspaceRole: "admin" | "member" = "member",
) {
  return {
    id: `test-org-${name}`,
    name,
    role,
    workspaces: Array.from({ length: count }, (_, index) => ({
      id: `test-workspace-${name}-${index}`,
      name: `${name} workspace ${index + 1}`,
      role: workspaceRole,
    })),
  };
}
async function tenantResponse(
  page: Page,
  organizations: ReturnType<typeof tenantOrganization>[],
) {
  await page.route("**/api/v1/me/context", (route) => {
    expect(route.request().headers()["authorization"]).toBe(`Bearer ${token}`);
    return route.fulfill({ json: { organizations } });
  });
}
test("tenant context auto-selects sole access and resets after logout", async ({
  page,
}) => {
  await mockServices(page);
  await login(page);
  await expect(page.locator(".desktop-sidebar")).toContainText(
    "Alpha workspace 1",
  );
  await page.getByRole("button", { name: "Account menu", exact: true }).click();
  await page.getByRole("menuitem", { name: "Sign out", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
  await tenantResponse(page, []);
  await login(page);
  await expect(
    page.getByRole("heading", { name: "No organization access yet" }),
  ).toBeVisible();
  await expect(page.getByText("Alpha workspace 1")).toHaveCount(0);
});
test("organization admins without workspace memberships have no workspace access", async ({
  page,
}) => {
  await mockServices(page);
  await tenantResponse(page, [tenantOrganization("Admin", 0)]);
  await login(page);
  await page.goto("/app/ask");
  await expect(
    page.getByRole("heading", { name: "No workspace access", exact: true }),
  ).toBeVisible();
});
test("explicit tenant selection ignores stored IDs, stays scoped and resets on reload", async ({
  page,
}) => {
  await page.addInitScript(() => {
    localStorage.setItem("organization_id", "unauthorized-org");
    localStorage.setItem("workspace_id", "unauthorized-workspace");
  });
  await mockServices(page);
  await tenantResponse(page, [
    tenantOrganization("Alpha", 2),
    tenantOrganization("Beta", 1),
  ]);
  await login(page);
  await expect(
    page.getByRole("heading", { name: "Select an organization" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Organization", exact: true })
    .selectOption("test-org-Alpha");
  await page
    .getByRole("navigation", { name: "Main" })
    .getByRole("link", { name: "Ask Bismark", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Select a workspace" }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Workspace", exact: true })
    .selectOption("test-workspace-Alpha-1");
  await expect(
    page.getByRole("heading", { name: "Select a workspace" }),
  ).toHaveCount(0);
  await page.getByRole("link", { name: "Documents", exact: true }).click();
  await expect(
    page.getByRole("combobox", { name: "Workspace", exact: true }),
  ).toHaveValue("test-workspace-Alpha-1");
  await page
    .getByRole("combobox", { name: "Organization", exact: true })
    .selectOption("test-org-Beta");
  await expect(page.locator(".desktop-sidebar")).toContainText(
    "Beta workspace 1",
  );
  await expect(
    page.getByRole("combobox", { name: "Workspace", exact: true }),
  ).toHaveCount(0);
  await page
    .getByRole("combobox", { name: "Organization", exact: true })
    .selectOption("test-org-Alpha");
  await expect(
    page.getByRole("combobox", { name: "Workspace", exact: true }),
  ).toHaveValue("");
  await page.reload();
  await expect(
    page.getByRole("combobox", { name: "Organization", exact: true }),
  ).toHaveValue("");
});
for (const failure of [401, 500, "network"] as const) {
  test(`tenant context handles ${failure} and retries safely`, async ({
    page,
  }) => {
    await mockServices(page);
    await page.route("**/api/v1/me/context", (route) =>
      failure === "network"
        ? route.abort()
        : route.fulfill({ status: failure, json: {} }),
    );
    await login(page);
    await expect(page.getByRole("main").getByRole("alert")).toContainText(
      failure === 401
        ? "Your session could not be verified"
        : "We couldn’t load your workspace access",
    );
    await tenantResponse(page, [tenantOrganization("Recovered", 1)]);
    await page.getByRole("button", { name: "Retry workspace access" }).click();
    await expect(page.locator(".desktop-sidebar")).toContainText(
      "Recovered workspace 1",
    );
  });
}

for (const role of ["owner", "admin"] as const) {
  test(`${role} sees full tenant navigation and can open admin routes`, async ({
    page,
  }) => {
    await mockServices(page, false, false, [
      tenantOrganization("Alpha", 1, role),
    ]);
    await login(page);
    await expect(page).toHaveURL(/\/app$/);
    const navigation = page
      .locator(".desktop-sidebar")
      .getByRole("navigation", {
        name: "Main",
      });
    for (const label of [
      "Overview",
      "Ask Bismark",
      "Sources",
      "Documents",
      "Conversations",
      "Members",
      "Analytics",
      "Usage",
      "Settings",
    ])
      await expect(navigation.getByRole("link", { name: label })).toBeVisible();

    await page.goto("/app/members");
    await expect(page.locator("#app-content h1")).toHaveText("Members");
  });
}

test("organization member sees only chat navigation and is denied admin routes", async ({
  page,
}) => {
  await mockServices(page, false, false, [
    tenantOrganization("Member", 1, "member"),
  ]);
  await login(page);
  await expect(page).toHaveURL(/\/app\/ask$/);

  const navigation = page.locator(".desktop-sidebar").getByRole("navigation", {
    name: "Main",
  });
  await expect(
    navigation.getByRole("link", { name: "Ask Bismark" }),
  ).toBeVisible();
  await expect(
    navigation.getByRole("link", { name: "Conversations" }),
  ).toBeVisible();
  for (const label of [
    "Overview",
    "Sources",
    "Documents",
    "Members",
    "Analytics",
    "Usage",
    "Settings",
  ])
    await expect(navigation.getByRole("link", { name: label })).toHaveCount(0);

  await page.goto("/app/sources");
  await expect(page).toHaveURL(/\/app\/ask$/);
  await expect(page.locator("#app-content h1")).not.toHaveText(
    "Knowledge sources",
  );
});

test("organization member visiting app root is redirected to Ask Bismark", async ({
  page,
}) => {
  await mockServices(page, false, false, [
    tenantOrganization("Member", 1, "member"),
  ]);
  await login(page);
  await expect(page).toHaveURL(/\/app\/ask$/);
  await expect(page.locator("#app-content h1")).toHaveText("Ask Bismark");
});

test("loading tenant context does not redirect a pending admin route", async ({
  page,
}) => {
  await mockServices(page);
  let releaseContext!: () => void;
  const contextPending = new Promise<void>((resolve) => {
    releaseContext = resolve;
  });
  await page.route("**/api/v1/me/context", async (route) => {
    await contextPending;
    await route.fulfill({
      json: { organizations: [tenantOrganization("Alpha", 1, "admin")] },
    });
  });
  await login(page);
  await expect(page.getByRole("status")).toContainText(
    "Loading workspace access",
  );
  await page.goto("/app/sources");
  await expect(page).toHaveURL(/\/app\/sources$/);
  releaseContext();
  await expect(page.locator("#app-content h1")).toHaveText("Knowledge sources");
});

test("no-workspace state is truthful and account route remains available", async ({
  page,
}) => {
  await mockServices(page, false, false, [
    tenantOrganization("Admin", 0, "owner"),
  ]);
  await login(page);
  await page.goto("/app/ask");
  await expect(
    page.getByRole("heading", { name: "No workspace access" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Account menu" }),
  ).toBeVisible();
  await page.goto("/app/account");
  await expect(page.locator("#app-content h1")).toHaveText("Account");
});

test("workspace admin with organization member role does not receive admin access", async ({
  page,
}) => {
  await mockServices(page, false, false, [
    tenantOrganization("MemberWorkspaceAdmin", 1, "member", "admin"),
  ]);
  await login(page);
  await expect(page).toHaveURL(/\/app\/ask$/);
  const navigation = page.locator(".desktop-sidebar").getByRole("navigation", {
    name: "Main",
  });
  await expect(navigation.getByRole("link", { name: "Sources" })).toHaveCount(
    0,
  );
  await page.goto("/app/settings");
  await expect(page).toHaveURL(/\/app\/ask$/);
});

for (const role of ["admin", "member"] as const) {
  test(`mobile navigation for ${role} keeps account/sign-out and filters tenant links`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await mockServices(page, false, false, [
      tenantOrganization("Mobile", 1, role),
    ]);
    await login(page);
    if (role === "member") await expect(page).toHaveURL(/\/app\/ask$/);
    await page.getByRole("button", { name: "Open navigation" }).click();
    const navigation = page
      .getByRole("dialog", { name: "Navigation" })
      .getByRole("navigation", { name: "Main" });
    await expect(
      navigation.getByRole("link", { name: "Ask Bismark" }),
    ).toBeVisible();
    if (role === "admin") {
      await expect(
        navigation.getByRole("link", { name: "Analytics" }),
      ).toBeVisible();
      await expect(
        navigation.getByRole("link", { name: "Settings" }),
      ).toBeVisible();
    } else {
      await expect(
        navigation.getByRole("link", { name: "Sources" }),
      ).toHaveCount(0);
      await expect(
        navigation.getByRole("link", { name: "Settings" }),
      ).toHaveCount(0);
    }
    const drawer = page.getByRole("dialog", { name: "Navigation" });
    await drawer.getByRole("button", { name: "Account menu" }).click();
    await expect(
      drawer.getByRole("menuitem", { name: "Sign out" }),
    ).toBeVisible();
    await expect(
      drawer.getByRole("menuitem", { name: "Account" }),
    ).toBeVisible();
  });
}
