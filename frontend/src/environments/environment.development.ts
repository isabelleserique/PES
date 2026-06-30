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
  production: false,
  apiUrl: runtimeApiUrl || 'http://localhost:8000',
};
