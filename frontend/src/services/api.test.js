import api, { healthApi, resolveHealthUrl, setAuthInitialization, warmBackend } from './api';

const originalAdapter = api.defaults.adapter;
const originalHealthAdapter = healthApi.defaults.adapter;

const successfulResponse = (config) => ({
  config,
  data: { ok: true },
  headers: {},
  status: 200,
  statusText: 'OK',
});

const failedResponse = (config, status) => {
  const error = new Error(`HTTP ${status}`);
  error.config = config;
  error.response = { config, data: {}, headers: {}, status, statusText: 'Unavailable' };
  return Promise.reject(error);
};

const networkFailure = (config) => {
  const error = new Error('Network Error');
  error.config = config;
  error.code = 'ERR_NETWORK';
  error.request = {};
  return Promise.reject(error);
};

afterEach(() => {
  api.defaults.adapter = originalAdapter;
  healthApi.defaults.adapter = originalHealthAdapter;
  setAuthInitialization(true);
});

test('resolves the production API base to the exact Render health endpoint', () => {
  expect(resolveHealthUrl('https://fintech-tax-ai.onrender.com/api'))
    .toBe('https://fintech-tax-ai.onrender.com/health');
});

test('keeps local API base configuration compatible with local health checks', () => {
  expect(resolveHealthUrl('http://localhost:5000/api')).toBe('http://localhost:5000/health');
});

test.each([502, 503, 504])('retries a GET after HTTP %i and accepts a successful response', async (status) => {
  let attempts = 0;
  api.defaults.adapter = jest.fn(config => {
    attempts += 1;
    return attempts === 1 ? failedResponse(config, status) : Promise.resolve(successfulResponse(config));
  });

  const request = api.get('health-probe');

  await expect(request).resolves.toMatchObject({ status: 200 });
  expect(attempts).toBe(2);
});

test('retries network errors with exponential backoff, up to three total attempts', async () => {
  let attempts = 0;
  api.defaults.adapter = jest.fn(config => {
    attempts += 1;
    return networkFailure(config);
  });

  const request = api.get('health-probe');

  await expect(request).rejects.toThrow('Network Error');
  expect(attempts).toBe(3);
});

test('does not retry a GET for HTTP errors outside 502, 503, and 504', async () => {
  let attempts = 0;
  api.defaults.adapter = jest.fn(config => {
    attempts += 1;
    return failedResponse(config, 500);
  });

  await expect(api.get('health-probe')).rejects.toMatchObject({ response: { status: 500 } });
  expect(attempts).toBe(1);
});

test('does not retry a timed-out GET as a network failure', async () => {
  let attempts = 0;
  api.defaults.adapter = jest.fn(config => {
    attempts += 1;
    const error = new Error('timeout');
    error.config = config;
    error.code = 'ECONNABORTED';
    error.request = {};
    return Promise.reject(error);
  });

  await expect(api.get('health-probe')).rejects.toMatchObject({ code: 'ECONNABORTED' });
  expect(attempts).toBe(1);
});

test.each(['post', 'put', 'patch', 'delete'])('does not retry %s requests', async (method) => {
  let attempts = 0;
  api.defaults.adapter = jest.fn(config => {
    attempts += 1;
    return failedResponse(config, 503);
  });

  await expect(api[method]('mutation')).rejects.toMatchObject({ response: { status: 503 } });
  expect(attempts).toBe(1);
});

test.each([
  'auth/login',
  'auth/register',
  'auth/send-registration-otp',
  'auth/verify-registration-otp',
  'auth/verify-otp',
  'auth/login/verify-otp',
  'auth/resend-otp',
  'auth/password-reset/request',
  'auth/password-reset/verify',
  'auth/password-reset/complete',
  'auth/registration/profile-photo',
  'auth/refresh',
])('does not refresh-and-replay sensitive auth POST %s after 401', async (route) => {
  let routeAttempts = 0;
  let refreshAttempts = 0;
  setAuthInitialization(false);
  api.defaults.adapter = jest.fn(config => {
    if (config.url === route) {
      routeAttempts += 1;
      return failedResponse(config, 401);
    }
    if (config.url === 'auth/refresh') {
      refreshAttempts += 1;
      return Promise.resolve({ ...successfulResponse(config), data: { access_token: 'refreshed' } });
    }
    return failedResponse(config, 401);
  });

  await expect(api.post(route, {})).rejects.toMatchObject({ response: { status: 401 } });
  expect(routeAttempts).toBe(1);
  expect(refreshAttempts).toBe(0);
});

test('preserves refresh-and-replay for an ordinary protected POST', async () => {
  let resourceAttempts = 0;
  let refreshAttempts = 0;
  setAuthInitialization(false);
  api.defaults.adapter = jest.fn(config => {
    if (config.url === 'auth/refresh') {
      refreshAttempts += 1;
      return Promise.resolve({ ...successfulResponse(config), data: { access_token: 'refreshed' } });
    }
    resourceAttempts += 1;
    return resourceAttempts === 1
      ? failedResponse(config, 401)
      : Promise.resolve(successfulResponse(config));
  });

  await expect(api.post('tax/filings', { amount: 10 })).resolves.toMatchObject({ status: 200 });
  expect(refreshAttempts).toBe(1);
  expect(resourceAttempts).toBe(2);
});

test('health-check failure is non-throwing and reports the backend unavailable', async () => {
  let attempts = 0;
  const warmFinishedListener = jest.fn();
  const unavailableListener = jest.fn();
  window.addEventListener('taxmate:api-warming-finished', warmFinishedListener);
  window.addEventListener('taxmate:api-unavailable', unavailableListener);
  healthApi.defaults.adapter = jest.fn(config => {
    attempts += 1;
    return failedResponse(config, 503);
  });

  const check = warmBackend();

  await expect(check).resolves.toBe(false);
  expect(attempts).toBe(3);
  expect(warmFinishedListener).toHaveBeenCalledWith(expect.objectContaining({ detail: { available: false } }));
  expect(unavailableListener).toHaveBeenCalled();
  window.removeEventListener('taxmate:api-warming-finished', warmFinishedListener);
  window.removeEventListener('taxmate:api-unavailable', unavailableListener);
});

test('successful warm-up completes and clears the loading state', async () => {
  const warmingListener = jest.fn();
  const warmFinishedListener = jest.fn();
  window.addEventListener('taxmate:api-warming', warmingListener);
  window.addEventListener('taxmate:api-warming-finished', warmFinishedListener);
  healthApi.defaults.adapter = jest.fn(config => Promise.resolve(successfulResponse(config)));

  await expect(warmBackend()).resolves.toBe(true);

  expect(warmingListener).toHaveBeenCalled();
  expect(warmFinishedListener).toHaveBeenCalledWith(expect.objectContaining({ detail: { available: true } }));
  window.removeEventListener('taxmate:api-warming', warmingListener);
  window.removeEventListener('taxmate:api-warming-finished', warmFinishedListener);
});

test('health-check failure does not invoke shared authentication refresh interceptors', async () => {
  let healthAttempts = 0;
  const sharedAdapter = jest.fn(config => {
    if (config.url === 'auth/refresh') {
      return Promise.resolve({ ...successfulResponse(config), data: { access_token: 'refreshed' } });
    }
    return failedResponse(config, 401);
  });
  setAuthInitialization(false);
  api.defaults.adapter = sharedAdapter;
  healthApi.defaults.adapter = jest.fn(config => {
    healthAttempts += 1;
    return failedResponse(config, 401);
  });

  await expect(warmBackend()).resolves.toBe(false);

  expect(healthAttempts).toBe(1);
  expect(sharedAdapter).not.toHaveBeenCalled();
});