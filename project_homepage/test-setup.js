// Simple test script to verify the setup
const { execSync } = require('child_process');

console.log('🧪 Testing Moodsprite Next.js Setup...\n');

try {
  // Test 1: Check if TypeScript compiles
  console.log('1. Testing TypeScript compilation...');
  execSync('npx tsc --noEmit', { stdio: 'pipe' });
  console.log('✅ TypeScript compilation successful\n');

  // Test 2: Check if Prisma generates client
  console.log('2. Testing Prisma client generation...');
  execSync('npx prisma generate', { stdio: 'pipe' });
  console.log('✅ Prisma client generation successful\n');

  // Test 3: Check if Next.js builds
  console.log('3. Testing Next.js build...');
  execSync('npm run build', { stdio: 'pipe' });
  console.log('✅ Next.js build successful\n');

  console.log('🎉 All tests passed! The setup is ready.');
  console.log('\nNext steps:');
  console.log('1. Set up your Clerk authentication keys in .env.local');
  console.log('2. Run: docker-compose up --build');
  console.log('3. Run: npx prisma migrate dev');
  console.log('4. Open http://localhost:3000');

} catch (error) {
  console.error('❌ Test failed:', error.message);
  process.exit(1);
}
