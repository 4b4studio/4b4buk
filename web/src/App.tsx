import { MatchPage } from "./pages/Match";
import { TodayPage } from "./pages/Today";
import { navigate, useLocation } from "./router";

export function App() {
  const { pathname, search } = useLocation();
  const matchRoute = /^\/mecz\/([^/]+)\/?$/.exec(pathname);
  return (
    <>
      <nav className="topbar">
        <button type="button" className="brand" onClick={() => navigate("/")}>
          4b4<span>buk</span>
        </button>
      </nav>
      {matchRoute ? (
        <MatchPage id={decodeURIComponent(matchRoute[1])} pathname={pathname} search={search} />
      ) : (
        <TodayPage search={search} />
      )}
    </>
  );
}
