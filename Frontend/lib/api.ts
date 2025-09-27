// Travel_Frontend/lib/api.ts
import axios from "axios";

// ---------------- CONFIG ----------------

const TARGET: "local" | "local" = "local";

const API_TARGETS: Record<string, string> = {
  local: "http://127.0.0.1:8000",

};

const API_BASE_URL: string = API_TARGETS[TARGET];

// Mock toggle (optional)
const USE_MOCK: boolean = false;

// ---------------- TYPES ----------------
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

// ---------------- MOCK RESPONSES ----------------
const mockResponses: Record<string, string> = {
  packing: `For a 5-day winter trip to Paris, I recommend packing:\n\n**Essentials:**\n• Warm coat\n• Layered clothing\n• Comfortable walking shoes\n• Umbrella\n• Scarf and gloves`,
  attractions: `Must-see attractions in Paris:\n\n• Eiffel Tower\n• Louvre Museum\n• Notre-Dame Cathedral\n• Arc de Triomphe`,
  destination: `For a romantic getaway, try:\n\n• Santorini, Greece\n• Tuscany, Italy\n• Prague, Czech Republic\n• Maldives`,
  weather: `Please provide:\n\n• Destination\n• Time of year\n• Trip length\n\nThen I can give specific advice!`,
  budget: `General budget breakdown:\n\n**Budget travel:** $50–100/day\n**Mid-range:** $150–300/day\n**Luxury:** $500+/day`,
  default: `Hi 👋 I'm your travel assistant!\n\nI can help with:\n• Destination ideas\n• Packing lists\n• Local attractions\n• Weather advice\n• Budget planning\n\nWhere are you planning to go?`,
};

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function sendMockMessage(text: string): Promise<ApiResponse> {
  await delay(800 + Math.random() * 1200);
  return {
    answer: mockResponses.default,
    followup: "Would you like more details?",
    context: { mock: true },
  };
}

// ---------------- REAL BACKEND ----------------
async function sendRealMessage(text: string): Promise<ApiResponse> {
  try {
    const res = await axios.post<ApiResponse>(
      `${API_BASE_URL}/assistant/ask`,
      { text },
      {
        headers: { "Content-Type": "application/json" },
        timeout: 120000,
      }
    );

    return {
      answer: String(res.data.answer ?? ""),
      followup: res.data.followup ?? undefined,
      context: res.data.context ?? {},
    };
  } catch (err) {
    console.error("❌ API Error:", err);
    throw new Error(`⚠️ Failed to reach backend at ${API_BASE_URL}`);
  }
}

// ---------------- MAIN EXPORT ----------------
export const sendMessage = async (text: string): Promise<ApiResponse> => {
  if (USE_MOCK) {
    return sendMockMessage(text);
  }
  return sendRealMessage(text);
};
