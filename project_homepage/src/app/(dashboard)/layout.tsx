import { MenuBar } from '@/components/menu-bar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <MenuBar />
      <main className="pt-16">
        {children}
      </main>
    </div>
  );
}
