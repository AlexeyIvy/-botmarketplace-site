"use client";

import { ChatWidget } from "./ChatWidget";

/**
 * Thin "use client" wrapper that allows ChatWidget to be mounted from
 * the server-component root layout without making the entire layout
 * a client component.
 */
export function ChatWidgetWrapper() {
  return <ChatWidget />;
}
