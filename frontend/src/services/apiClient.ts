import axios, { AxiosError } from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:5270/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ title?: string; detail?: string }>) => {
    const problemDetails = error.response?.data;
    const message =
      problemDetails?.detail ??
      problemDetails?.title ??
      error.message ??
      'An unexpected error occurred.';

    return Promise.reject(new Error(message));
  },
);

export default apiClient;
