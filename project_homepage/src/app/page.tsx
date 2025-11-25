import { redirect } from 'next/navigation';

export default function Home() {
  // Redirect to sprite view by default
  redirect('/sprite');
}
