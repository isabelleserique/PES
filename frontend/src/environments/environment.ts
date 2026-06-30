type RuntimeEnvironment = {
  apiUrl?: string;
};

declare global {
  interface Window {
    __tccompEnv?: RuntimeEnvironment;
  }
}

const runtimeApiUrl = typeof window !== 'undefined' ? window.__tccompEnv?.apiUrl : undefined;

export const environment = {
  production: true,
  apiUrl: runtimeApiUrl || 'http://localhost:8000',
};
