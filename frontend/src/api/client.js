import axios from "axios";

const client = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 10_000,
});

/**
 * Flattens FastAPI/Pydantic's 422 `detail` array into a single readable
 * string so components can show one message instead of a raw error object.
 */
function formatValidationError(detail) {
  if (!Array.isArray(detail)) return String(detail);
  return detail
    .map((item) => {
      const field = Array.isArray(item.loc) ? item.loc.at(-1) : "field";
      return `${field}: ${item.msg}`;
    })
    .join("; ");
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;
      if (status === 422 && data?.detail) {
        return Promise.reject(new Error(formatValidationError(data.detail)));
      }
      return Promise.reject(
        new Error(data?.detail || `Request failed with status ${status}`)
      );
    }
    if (error.request) {
      return Promise.reject(
        new Error("Could not reach the tax engine API. Is the backend running?")
      );
    }
    return Promise.reject(error);
  }
);

export const calculateTax = (payload) =>
  client.post("/calculate", payload).then((res) => res.data);

export const compareRegimes = (payload) =>
  client.post("/compare", payload).then((res) => res.data);

export default client;
