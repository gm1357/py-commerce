import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  // Exported by `api#openapi` (turbo runs it before `generate`).
  input: "../../apps/api/openapi.json",
  output: "src/client",
  plugins: [
    {
      name: "@hey-api/client-next",
      runtimeConfigPath: "./src/hey-api",
    },
  ],
});
