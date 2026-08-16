type Props = { title: string };

export function CmsTitle({ title }: Props) {
  return (
    <div className="flex h-5 items-center pl-3">
      <span className="text-sm font-medium">{title}</span>
    </div>
  );
}