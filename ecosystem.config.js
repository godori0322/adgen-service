module.exports = {
  apps: [
    {
      name: "backend",
      script: "uvicorn",
      args: "backend.app.main:app --host 0.0.0.0 --port 8500",
      interpreter: "none",
      cwd: "./backend",
    },
    {
      name: "frontend",
      script: "pnpm",
      args: "-c 'pnpm install && pnpm build && pnpm preview --host 0.0.0.0 --port 5173'",
      cwd: "./frontend",
      interpreter: "none",
      watch: false,
    },
  ],
};
