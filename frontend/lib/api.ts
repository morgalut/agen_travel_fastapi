// travel_assistant/frontend/lib/api.ts
import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export interface ApiResponse {
  answer: string;
  followup?: string;
  context: Record<string, any>;
}

export async function sendMessage(text: string): Promise<ApiResponse> {
  try {
    const res = await axios.post<ApiResponse>(
      `${API_BASE_URL}/assistant/ask`,
      { text }, // ⬅️ exactly like your curl
      { headers: { "Content-Type": "application/json" }, timeout: 20000 }
    );
    return res.data;
  } catch (err) {
    console.error("❌ API Error:", err);
    throw new Error(`⚠️ Could not reach backend at ${API_BASE_URL}`);
  }
}

// ✅ NEW: Reset conversation API
export async function resetConversation(): Promise<void> {
  try {
    await axios.post(
      `${API_BASE_URL}/assistant/reset`,
      {},
      { headers: { "Content-Type": "application/json" }, timeout: 10000 }
    );
    console.log("🗑️ Conversation reset on backend");
  } catch (err) {
    console.error("❌ Failed to reset conversation:", err);
  }
}
