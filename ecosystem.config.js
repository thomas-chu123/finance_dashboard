module.exports = {
  apps: [
    {
      name: 'finance-backend',
      cwd: './backend',
      script: '../venv/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8005',
      watch: false,
      env: {
        PYTHONPATH: '.',
        NODE_ENV: 'production',
      },
    },
    {
      name: 'finance-frontend',
      script: 'serve',
      env: {
        PM2_SERVE_PATH: './frontend/dist',
        PM2_SERVE_PORT: 3100,
        PM2_SERVE_SPA: 'true',
        PM2_SERVE_HOMEPAGE: '/index.html'
      }
    },
  ],
};
