"use client";

import { useState } from "react";
import { contactSchema, type ContactInput } from "@/lib/validations";

type FormStatus = "idle" | "loading" | "success" | "error";
type FieldErrors = Partial<Record<keyof ContactInput, string>>;

export function ContactForm() {
  const [status, setStatus] = useState<FormStatus>("idle");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const data = {
      name: String(formData.get("name") ?? ""),
      email: String(formData.get("email") ?? ""),
      subject: String(formData.get("subject") ?? ""),
      message: String(formData.get("message") ?? ""),
      website: String(formData.get("website") ?? ""),
    };

    const parsed = contactSchema.safeParse(data);
    if (!parsed.success) {
      const fieldErrors = parsed.error.flatten().fieldErrors;
      setErrors({
        name: fieldErrors.name?.[0],
        email: fieldErrors.email?.[0],
        subject: fieldErrors.subject?.[0],
        message: fieldErrors.message?.[0],
      });
      return;
    }

    setErrors({});
    setServerError(null);
    setStatus("loading");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed.data),
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as {
          error?: string;
        } | null;
        setServerError(body?.error ?? "Something went wrong. Please try again.");
        setStatus("error");
        return;
      }

      setStatus("success");
      form.reset();
    } catch {
      setServerError("Network error. Please try again.");
      setStatus("error");
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <label>
        Name
        <input
          required
          minLength={2}
          autoComplete="name"
          name="name"
          aria-invalid={Boolean(errors.name)}
        />
        {errors.name ? <span className="field-error">{errors.name}</span> : null}
      </label>
      <label>
        Email
        <input
          type="email"
          required
          autoComplete="email"
          name="email"
          aria-invalid={Boolean(errors.email)}
        />
        {errors.email ? (
          <span className="field-error">{errors.email}</span>
        ) : null}
      </label>
      <label>
        Subject
        <input
          required
          minLength={3}
          name="subject"
          aria-invalid={Boolean(errors.subject)}
        />
        {errors.subject ? (
          <span className="field-error">{errors.subject}</span>
        ) : null}
      </label>
      <label className="honeypot" aria-hidden="true">
        Website
        <input tabIndex={-1} autoComplete="off" name="website" />
      </label>
      <label>
        Message
        <textarea
          name="message"
          required
          minLength={10}
          rows={4}
          aria-invalid={Boolean(errors.message)}
        />
        {errors.message ? (
          <span className="field-error">{errors.message}</span>
        ) : null}
      </label>
      <button disabled={status === "loading"}>
        {status === "loading" ? "Sending…" : "Start a conversation"}
      </button>
      <p
        className={status === "error" ? "form-status error" : "form-status"}
        role="status"
        aria-live="polite"
      >
        {status === "success"
          ? "Message sent — I will get back to you soon."
          : null}
        {status === "error" ? serverError : null}
      </p>
    </form>
  );
}
