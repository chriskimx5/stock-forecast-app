export function getApiBase() {
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    const backend = params.get("backend");

    if (backend) {
      return `${backend.replace(/\/$/, "")}/api/v1`;
    }

    const runtimeApiBase = (window as any).__API_BASE__;
    if (runtimeApiBase) {
      return runtimeApiBase;
    }
  }

  return process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";
}