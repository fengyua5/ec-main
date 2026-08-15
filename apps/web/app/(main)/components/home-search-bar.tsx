export function HomeSearchBar() {
  return (
    <div className="relative">
      <input
        type="text"
        placeholder="搜索商品…"
        className="w-full rounded-xl border bg-surface-100-bg px-4 py-3 pl-10 text-sm text-surface-100-fg-default outline-none placeholder:text-surface-100-fg-minor"
      />
      <svg
        className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-surface-100-fg-minor"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
        />
      </svg>
    </div>
  );
}