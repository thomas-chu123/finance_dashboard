const path = require('path');

module.exports = {
  apps: [
    {
      name: 'finance-backend',
      cwd: path.resolve(__dirname, './backend'),
      script: path.resolve(__dirname, './venv/bin/python'),
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8005',
      watch: false,
      env: {
        PYTHONPATH: path.resolve(__dirname, './backend'),
        NODE_ENV: 'production',
      },
    },
    {
      name: 'finance-frontend',
      script: 'serve',
      env: {
        PM2_SERVE_PATH: path.resolve(__dirname, './frontend/dist'),
        PM2_SERVE_PORT: 3100,
        PM2_SERVE_SPA: 'true',
        PM2_SERVE_HOMEPAGE: '/index.html'
      }
    },
  ],
};
