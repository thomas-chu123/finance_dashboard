const path = require('path');

module.exports = {
  apps: [
    {
      name: 'finance-backend',
      cwd: path.resolve(__dirname, './backend'),
      script: path.resolve(__dirname, './venv/bin/python'),
      args: '-u -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --access-log',
      watch: false,
      time: true,
      env: {
        PYTHONPATH: path.resolve(__dirname, './backend'),
        NODE_ENV: 'production',
      },
    },
    {
      name: 'finance-frontend',
      script: path.resolve(__dirname, './frontend/server.cjs'),
      time: true,
      env: {
        PM2_SERVE_PORT: 3100,
      }
    },
  ],
};
