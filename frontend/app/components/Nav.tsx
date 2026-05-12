"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Chart" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/signals", label: "Signals" },
  { href: "/positions", label: "Positions" },
  { href: "/journal", label: "Journal" },
];

export default function Nav() {
  const pathname = usePathname();
  return (
    <nav style={{ display: "flex", gap: 8, padding: "12px 24px", borderBottom: "1px solid #eee", fontFamily: "system-ui" }}>
      {links.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          style={{
            padding: "6px 14px",
            borderRadius: 8,
            textDecoration: "none",
            background: pathname === l.href ? "#000" : "transparent",
            color: pathname === l.href ? "#fff" : "#333",
            fontSize: 14,
            fontWeight: pathname === l.href ? 600 : 400,
          }}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
