// pm2 ecosystem config — 卧龙 Agent 进程守护
// 启动: pm2 start ecosystem.config.cjs
// 重启: pm2 restart all
// 状态: pm2 status
// 日志: pm2 logs

const path = require('path')
const ROOT = __dirname

// 从 .env 文件加载环境变量
const fs = require('fs')
const envPath = path.join(ROOT, '.env')
const env = {}
if (fs.existsSync(envPath)) {
  fs.readFileSync(envPath, 'utf-8').split('\n').forEach(line => {
    line = line.trim()
    if (!line || line.startsWith('#')) return
    const idx = line.indexOf('=')
    if (idx > 0) {
      env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim()
    }
  })
}

module.exports = {
  apps: [
    {
      name: 'wolong-api',
      script: 'python3',
      args: 'scripts/api_server.py --port=8765',
      cwd: ROOT,
      env: {
        ...env,
        HTTPS_PROXY: 'http://127.0.0.1:40009',
        HTTP_PROXY:  'http://127.0.0.1:40009',
      },
      watch: false,
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
      log_file: '/tmp/wolong-api.log',
      error_file: '/tmp/wolong-api-err.log',
      merge_logs: true,
    },
    {
      name: 'wolong-h5',
      script: 'node',
      args: 'node_modules/.bin/vite --port 5173',
      cwd: path.join(ROOT, 'wolong_h5_console'),  // 主仓库，worktree 已删除
      env: { NODE_ENV: 'development' },
      watch: false,
      autorestart: true,
      restart_delay: 3000,
      max_restarts: 20,
      log_file: '/tmp/wolong-h5.log',
      error_file: '/tmp/wolong-h5-err.log',
      merge_logs: true,
    },
    {
      // ngrok 需要不带代理启动，否则报 ERR_NGROK_9009
      name: 'wolong-ngrok',
      script: 'ngrok',
      args: 'http 8765 --url=porter-unsimultaneous-nonopprobriously.ngrok-free.dev --log=stdout',
      cwd: ROOT,
      env: {
        // 显式清除代理，防止系统代理干扰 ngrok
        HTTPS_PROXY: '',
        HTTP_PROXY:  '',
        http_proxy:  '',
        https_proxy: '',
      },
      watch: false,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10,
      log_file: '/tmp/wolong-ngrok.log',
      error_file: '/tmp/wolong-ngrok-err.log',
      merge_logs: true,
    },
  ],
}
