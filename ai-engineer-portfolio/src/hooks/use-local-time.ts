"use client";

import { useEffect, useState } from "react";

const formatter = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Asia/Kolkata",
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});

export function getIndiaTime() {
  return formatter.format(new Date()).toLowerCase();
}

export function useLocalTime() {
  const [time, setTime] = useState("—");

  useEffect(() => {
    const tick = () => setTime(getIndiaTime());
    tick();
    const id = window.setInterval(tick, 30_000);
    return () => window.clearInterval(id);
  }, []);

  return time;
}
