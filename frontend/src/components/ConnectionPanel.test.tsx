import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../api/client", () => ({
  api: {
    getConnection: vi.fn().mockResolvedValue({
      connected: false,
      env_available: true,
      env_defaults: {
        endpoint: "http://localhost:8529",
        database: "_system",
        username: "root",
        has_password: true,
      },
      current: null,
    }),
    testConnection: vi.fn(),
    setConnection: vi.fn(),
    clearConnection: vi.fn(),
  },
}));

import { ConnectionProvider } from "../context/ConnectionContext";
import ConnectionPanel from "./ConnectionPanel";

function renderPanel() {
  return render(
    <ConnectionProvider>
      <ConnectionPanel />
    </ConnectionProvider>,
  );
}

describe("ConnectionPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("defaults to .env mode and shows the env defaults", async () => {
    renderPanel();
    expect(await screen.findByText("endpoint: http://localhost:8529")).toBeInTheDocument();
    // Manual-only fields are not visible in env mode.
    expect(screen.queryByLabelText(/Endpoint \/ URI/)).not.toBeInTheDocument();
  });

  it("switches to manual mode and reveals credential fields", async () => {
    renderPanel();
    await screen.findByText("endpoint: http://localhost:8529");

    await userEvent.click(screen.getByRole("button", { name: /Manual/ }));

    await waitFor(() => {
      expect(screen.getByLabelText(/Endpoint \/ URI/)).toBeInTheDocument();
    });
    expect(screen.getByLabelText(/Password/)).toBeInTheDocument();
  });
});
