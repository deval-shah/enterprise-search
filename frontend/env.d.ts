// env.d.ts or custom-env.d.ts
declare namespace NodeJS {
    interface ProcessEnv {
      NEXT_PUBLIC_API_URL: string;
      // Add other environment variables here
    }
  }  