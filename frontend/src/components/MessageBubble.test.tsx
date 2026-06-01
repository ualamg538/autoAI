import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { Block } from "../lib/api";
import MessageBubble from "./MessageBubble";

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

describe("MessageBubble", () => {
  it("role 'user' muestra el texto plano", () => {
    render(<MessageBubble role="user" content="¿Qué SUV me recomiendas?" />);
    expect(
      screen.getByText("¿Qué SUV me recomiendas?"),
    ).toBeInTheDocument();
  });

  it("role 'assistant' con TextBlock renderiza el markdown como texto", () => {
    const blocks: Block[] = [
      { type: "text", content: "El **Corolla** es una buena opción." },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    // react-markdown convierte **Corolla** en <strong>; el texto sigue presente.
    expect(screen.getByText("Corolla")).toBeInTheDocument();
    expect(screen.getByText("Corolla").tagName).toBe("STRONG");
  });

  it("ImageBlock con foto_url renderiza un <img> con ese src", () => {
    const blocks: Block[] = [
      {
        type: "image",
        car_id: 1,
        caption: "Toyota Corolla",
        foto_url: "https://example.test/corolla.jpg",
      },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAttribute("src", "https://example.test/corolla.jpg");
    expect(img).toHaveAttribute("alt", "Toyota Corolla");
  });

  it("ImageBlock sin foto_url no renderiza imagen", () => {
    const blocks: Block[] = [
      { type: "image", car_id: 1, caption: "sin foto" },
    ];
    render(<MessageBubble role="assistant" blocks={blocks} />);
    expect(screen.queryByRole("img")).toBeNull();
  });
});
