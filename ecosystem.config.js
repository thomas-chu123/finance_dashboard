module.exports = {
  apps: [
    {
      name: 'finance-backend',
      cwd: './backend',
      script: 'uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8005',
      interpreter: '../venv/bin/python', // 位於專案根目錄的 venv
      watch: false,
      env: {
        NODE_ENV: 'production',
      },
    },
    {
      name: 'finance-frontend',
      script: 'serve',
      env: {
        PM2_SERVE_PATH: './frontend/dist',
        PM2_SERVE_PORT: 3000,
        PM2_SERVE_SPA: 'true',
        PM2_SERVE_HOMEPAGE: '/index.html'
      }
    },
  ],
};
