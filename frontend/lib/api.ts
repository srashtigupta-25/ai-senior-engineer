import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function indexRepository(repoUrl: string) {
  const response = await axios.post(`${API_BASE_URL}/repository/clone`, {
    repo_url: repoUrl,
  });

  return response.data;
}

export async function askRepository(question: string) {
  const response = await axios.post(`${API_BASE_URL}/chat/ask`, {
    question,
  });

  return response.data;
}

export async function getArchitecture() {
  const response = await axios.get(`${API_BASE_URL}/analysis/architecture`);

  return response.data;
}

export async function getOnboarding() {
  const response = await axios.get(`${API_BASE_URL}/analysis/onboarding`);

  return response.data;
}