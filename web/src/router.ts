import { useEffect, useState } from "react";

// A dependency-free router: two screens do not justify a routing library yet.
export interface Location { pathname: string; search: string }

const read = (): Location => ({ pathname: window.location.pathname, search: window.location.search });

export function useLocation(): Location {
  const [location, setLocation] = useState<Location>(read);
  useEffect(() => {
    const update = () => setLocation(read());
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return location;
}

export function navigate(to: string, options: { replace?: boolean } = {}): void {
  if (to === window.location.pathname + window.location.search) return;
  if (options.replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
  if (!options.replace) window.scrollTo(0, 0);
}
