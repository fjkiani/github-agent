const { execSync } = require('child_process');
const axios = require('axios');

describe('Docker Container Tests', () => {
  const containerName = 'app-test-container';
  
  beforeAll(async () => {
    // Build the Docker image
    execSync('docker build -t app-test-image .');
    
    // Run the container
    execSync(`docker run -d --name ${containerName} -p 3000:3000 app-test-image`);
    
    // Wait for container to start
    await new Promise(resolve => setTimeout(resolve, 5000));
  });

  afterAll(() => {
    // Clean up: Stop and remove the container
    try {
      execSync(`docker stop ${containerName}`);
      execSync(`docker rm ${containerName}`);
    } catch (error) {
      console.error('Cleanup error:', error);
    }
  });

  test('container should be running and app should be accessible', async () => {
    const response = await axios.get('http://localhost:3000');
    expect(response.status).toBe(200);
  });
}); 