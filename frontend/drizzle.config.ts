import { type Config } from "drizzle-kit";
import * as dotenv from "dotenv";
import { resolve } from "path";

// Load environment variables from .env file
dotenv.config({ path: resolve(__dirname, ".env") });

// Check if DATABASE_URL is defined
const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DATABASE_URL is not defined in environment variables");
}

export default {
  schema: "./src/server/db/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url: databaseUrl,
  },
} satisfies Config;
