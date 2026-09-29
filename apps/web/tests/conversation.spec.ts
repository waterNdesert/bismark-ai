import { test, expect } from "@playwright/test";
import { createElement as h } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { readFileSync } from "node:fs";
import {
  ConversationViewport,
  UserMessage,
  AssistantMessage,
  ResponseActions,
  SourceCitation,
  FollowUpSuggestions,
} from "../components/chat/conversation";

// Test-only fixture: never added to an application route or visible in the app.
for (const width of [1440, 1280, 768, 390]) {
  test(`conversation primitives and bottom composer at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 844 });
    const markup = renderToStaticMarkup(
      h(ConversationViewport, {
        composer: h(
          "div",
          { "data-testid": "composer" },
          h(
            "label",
            null,
            "Test draft",
            h("textarea", { "aria-label": "Test draft" }),
          ),
        ),
        children: [
          h(UserMessage, {
            key: "user",
            children: "Fixture question — not a real conversation.",
          }),
          h(AssistantMessage, {
            key: "answer",
            sources: h(SourceCitation, {
              name: "Fixture document",
              page: 14,
              section: "Test section",
              context: "Test context",
            }),
            actions: h(ResponseActions),
            followUps: h(FollowUpSuggestions, {
              suggestions: ["Fixture follow-up"],
            }),
            children: h(
              "div",
              null,
              h("h2", null, "Fixture answer"),
              ...Array.from({ length: 20 }, (_, index) =>
                h(
                  "p",
                  { key: index },
                  "Test paragraph for scroll and readable content verification.",
                ),
              ),
              h(
                "ul",
                null,
                h("li", null, h("strong", null, "Emphasized test point")),
              ),
              h(
                "p",
                { "data-testid": "final-message" },
                "Final fixture paragraph.",
              ),
            ),
          }),
        ],
      }),
    );
    const css = readFileSync("app/app/ask/ask.css", "utf8");
    await page.setContent(
      `<style>*{box-sizing:border-box}body{margin:0;background:#0c0d0e;color:#eee;font:14px Arial}button:disabled{cursor:not-allowed}${css}</style>${markup}`,
    );
    const dock = page.locator(".conversation-dock");
    const before = await dock.boundingBox();
    await page.getByRole("region", { name: "Messages" }).evaluate((element) => {
      element.scrollTop = element.scrollHeight;
    });
    expect(await dock.boundingBox()).toEqual(before);
    const actions = page.getByRole("group", { name: "Answer actions" });
    for (const label of ["Copy answer", "Regenerate", "Helpful", "Not helpful"])
      await expect(
        actions.getByRole("button", { name: label, exact: true }),
      ).toBeDisabled();
    await expect(
      page.getByRole("button", {
        name: "Source preview unavailable: Fixture document",
      }),
    ).toBeDisabled();
    await expect(
      page.getByRole("button", { name: "Fixture follow-up" }),
    ).toBeDisabled();
    await expect(page.getByText("p. 14 · Test section")).toBeVisible();
    const last = await page.getByTestId("final-message").boundingBox();
    expect(last!.y + last!.height).toBeLessThanOrEqual(before!.y);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: test.info().outputPath(`conversation-${width}.png`),
      fullPage: true,
    });
  });
}
