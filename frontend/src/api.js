// Centralized API client with base URL and helpers

import axios from "axios";

// Back-end runs at 8000 by default
export const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: { "Content-Type": "application/json" }
});

// Utility: log a user interaction (view/cart/purchase/rate)
export function createInteraction({ product_id, type, rating = null }) {
  return api.post("/interactions/", { product_id, type, rating });
}

// --- New: search & suggestions ---
export const searchProducts = (q, page=1) => api.get(`/search`, { params: { q, page } });
export const suggest = (q) => api.get(`/search/suggest`, { params: { q } });

// --- New: AI content for a product ---
export const genDescription = (id) => api.post(`/products/${id}/generate_description`);
export const summarizeReviews = (id) => api.post(`/products/${id}/summarize_reviews`);

// --- New: chatbot ---
export const chatReply = (history) => api.post("/chatbot/", { history });

// --- New: reviews ---
export const createReview = (data) => api.post(`/reviews/`, data);
export const listReviews = (productId) => api.get(`/reviews/`, { params: { product: productId } });

// --- New: JWT auth helpers ---
api.interceptors.request.use(config => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const getMe = () => api.get("/me/");

export function logout() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

// cart + checkout
export const getCart = () => api.get("/cart/");
export const addToCart = (product_id, qty=1) => api.post("/cart/add", { product_id, qty });
export const updateCartItem = (item_id, qty) => api.post("/cart/update", { item_id, qty });
export const checkout = () => api.post("/checkout/");

// frontend/src/api.js
export const getRecommendationsForMe = () =>
  api.get("/recommendations/me/").then(r => r.data);
