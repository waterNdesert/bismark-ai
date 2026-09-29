import type { Metadata } from "next";
import "./ask.css";
import { AskComposer } from "./ask-composer";
export const metadata: Metadata = { title: "Ask Bismark" };
export default function AskPage() {
  return <AskComposer />;
}
