module.exports = {
  apps: [
    {
      name: "backend",
      script: "uvicorn",
      args: "backend.app.main:app --host 0.0.0.0 --port 8080 --timeout-keep-alive 900",
      interpreter: "none",
      cwd: "./backend",
    },
    {
      name: "frontend",
      script: "pnpm",
      args: "start:pm2",
      cwd: "./frontend",
      interpreter: "none",
    },
  ],
};
