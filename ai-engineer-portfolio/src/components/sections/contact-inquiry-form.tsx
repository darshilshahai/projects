"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MagneticButton } from "@/components/motion/magnetic";
import { contactSchema, type ContactInput } from "@/lib/validations";

const fields = [
  { number: "01", name: "name", label: "What’s your name?", placeholder: "John Doe *", type: "text" },
  { number: "02", name: "email", label: "What’s your email?", placeholder: "john@doe.com *", type: "email" },
  { number: "03", name: "organization", label: "What’s the name of your organization?", placeholder: "John & Doe®", type: "text" },
  { number: "04", name: "services", label: "What services are you looking for?", placeholder: "AI product, RAG system, full-stack development…", type: "text" },
] as const;

type FieldErrors = Partial<Record<keyof ContactInput | "organization" | "services", string>>;

export function ContactInquiryForm() {
  const reduceMotion = useReducedMotion();
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [serverError, setServerError] = useState<string | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const payload = {
      name: String(data.get("name") ?? ""),
      email: String(data.get("email") ?? ""),
      subject: `${data.get("services") || "Portfolio enquiry"} — ${data.get("organization") || "Independent"}`,
      message: String(data.get("message") ?? ""),
      website: String(data.get("website") ?? ""),
    };

    const parsed = contactSchema.safeParse(payload);
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
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
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
    <form className="contact-inquiry-form" onSubmit={submit} noValidate>
      {fields.map((field, index) => (
        <motion.label
          key={field.name}
          initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.65, delay: 1.2 + index * 0.08 }}
        >
          <span>{field.number}</span>
          <div>
            <strong>{field.label}</strong>
            <input
              name={field.name}
              type={field.type}
              placeholder={field.placeholder}
              required={index < 2}
              autoComplete={field.name === "name" ? "name" : field.name === "email" ? "email" : "organization"}
              aria-invalid={Boolean(errors[field.name as keyof FieldErrors])}
            />
            {errors[field.name as keyof FieldErrors] ? (
              <span className="field-error">{errors[field.name as keyof FieldErrors]}</span>
            ) : null}
          </div>
        </motion.label>
      ))}
      <motion.label
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0, y: 28 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.65, delay: 1.52 }}
      >
        <span>05</span>
        <div>
          <strong>Your message</strong>
          <textarea
            name="message"
            placeholder="Hello Darshil, can you help me with… *"
            rows={3}
            minLength={10}
            required
            aria-invalid={Boolean(errors.message)}
          />
          {errors.message ? <span className="field-error">{errors.message}</span> : null}
        </div>
      </motion.label>
      <label className="honeypot" aria-hidden="true">
        <input name="website" tabIndex={-1} autoComplete="off" />
      </label>

      <div className="contact-send-row">
        <MagneticButton type="submit" disabled={status === "loading"} className="contact-send">
          {status === "loading" ? "Sending…" : status === "success" ? "Sent" : "Send it"}
        </MagneticButton>
      </div>
      <p className={`contact-page-status ${status}`} role="status" aria-live="polite">
        {status === "success" ? "Thanks — I’ll get back to you soon." : null}
        {status === "error" ? serverError : null}
      </p>
    </form>
  );
}
