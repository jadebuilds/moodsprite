import Link from 'next/link';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
            
            <div className="space-y-6">
              <div className="border-b border-gray-200 pb-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">General</h2>
                <p className="text-gray-600">
                  Settings coming soon... This is a placeholder for future configuration options.
                </p>
              </div>

              <div className="border-b border-gray-200 pb-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Character Preferences</h2>
                <p className="text-gray-600">
                  Character customization and mood preferences will be available here.
                </p>
              </div>

              <div className="border-b border-gray-200 pb-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">Notifications</h2>
                <p className="text-gray-600">
                  Notification settings and alerts configuration will be added here.
                </p>
              </div>

              <div className="pt-6">
                <Link
                  href="/sprite"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Back to Sprite View
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
