// The admin panel is the founder's own tool, not the gendered end-user
// experience — always render it in the neutral palette regardless of
// whatever preference happens to be stored in this browser.
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div data-gender="other" className="flex-1 flex flex-col">
      {children}
    </div>
  );
}
