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
      "/app/usage",
      "/app/settings",
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
      await expect(navigation.locator('[aria-current="page"]')).toHaveAttribute(
        "href",
        route,
      );
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
    await expect(
      page.getByRole("menuitem", { name: "Account & settings" }),
    ).toBeFocused();
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
    page.getByRole("dialog", { name: "Upload a document" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Choose a file" }),
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
