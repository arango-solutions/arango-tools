import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ToolSpec } from "../types";
import ToolForm, { initialValues } from "./ToolForm";

const spec: ToolSpec = {
  name: "demo",
  binary: "demo",
  title: "Demo",
  description: "",
  connects: true,
  doc_url: "",
  fields: [
    {
      key: "output_directory",
      flag: "--output-directory",
      type: "path",
      label: "Output directory",
      help: "",
      default: null,
      required: true,
      positional: false,
      repeatable: false,
      options: [],
      placeholder: "dump",
      group: "Common",
    },
    {
      key: "compress",
      flag: "--compress",
      type: "bool",
      label: "Compress",
      help: "",
      default: true,
      required: false,
      positional: false,
      repeatable: false,
      options: [],
      placeholder: "",
      group: "Common",
    },
    {
      key: "mode",
      flag: "--mode",
      type: "enum",
      label: "Mode",
      help: "",
      default: "json",
      required: false,
      positional: false,
      repeatable: false,
      options: ["json", "csv"],
      group: "Common",
      placeholder: "",
    },
  ],
};

describe("initialValues", () => {
  it("derives defaults from the spec", () => {
    const values = initialValues(spec);
    expect(values).toEqual({
      output_directory: "",
      compress: true,
      mode: "json",
    });
  });
});

describe("ToolForm", () => {
  it("renders a field per spec entry", () => {
    render(<ToolForm spec={spec} values={initialValues(spec)} onChange={() => {}} />);
    expect(screen.getByLabelText(/Output directory/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Compress/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Mode/)).toBeInTheDocument();
  });

  it("calls onChange when a text field is edited", async () => {
    const onChange = vi.fn();
    render(<ToolForm spec={spec} values={initialValues(spec)} onChange={onChange} />);
    await userEvent.type(screen.getByLabelText(/Output directory/), "d");
    expect(onChange).toHaveBeenCalledWith("output_directory", "d");
  });

  it("calls onChange when a checkbox is toggled", async () => {
    const onChange = vi.fn();
    render(<ToolForm spec={spec} values={initialValues(spec)} onChange={onChange} />);
    await userEvent.click(screen.getByLabelText(/Compress/));
    expect(onChange).toHaveBeenCalledWith("compress", false);
  });
});
