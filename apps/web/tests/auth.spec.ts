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
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
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
