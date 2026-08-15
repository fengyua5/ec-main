import type { Announcement } from "@ec/sdk";

type Props = { items: Announcement[] };

export function HomeAnnouncement({ items }: Props) {
  if (items.length === 0) return null;
  return (
    <div className="space-y-2">
      {items.map((item) => (
        <p
          key={item.id}
          className="rounded-lg bg-surface-100-bg px-4 py-2 text-sm text-surface-100-fg-minor"
        >
          {item.content}
        </p>
      ))}
    </div>
  );
}
