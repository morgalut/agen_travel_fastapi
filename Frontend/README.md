# Travel Assistant Frontend

A modern, conversational frontend for the Travel Assistant API. Built with Next.js, TypeScript, and Tailwind CSS.

## ✨ Features

- 🤖 **Conversational Interface**: Natural chat experience with your travel assistant
- 🎨 **Modern UI**: Clean, responsive design with smooth animations and beautiful gradients
- ⚡ **Mock Data Mode**: Works out-of-the-box with realistic mock responses for demo purposes
- 🔄 **Easy Backend Integration**: Simple switch to connect to your real backend API
- 🛡️ **Error Handling**: Graceful error handling for connection issues and timeouts
- 📱 **Responsive Design**: Works perfectly on desktop and mobile devices
- 🎯 **Smart Responses**: Context-aware responses based on keywords in user messages
- ✨ **Rich Formatting**: Supports markdown-style formatting for better readability

## 🚀 Quick Start (Demo Mode)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

4. **Try the demo:**
   - Click on any of the quick question buttons
   - Type your own travel questions
   - Experience the conversational interface with realistic mock responses

## 🔌 Backend Integration

### Current Setup (Mock Mode)
The frontend currently runs in **mock mode** with realistic sample responses. This allows you to:
- Test the UI and user experience immediately
- See how the conversation flow works
- Demo the application without needing a backend

### Switching to Real Backend

To connect to your actual backend API, follow these steps:

#### 1. Update the API Configuration

Edit `lib/api.ts` and uncomment the real API code:

```typescript
export const sendMessage = async (text: string): Promise<ApiResponse> => {
  // Comment out the mock data section
  /*
  await delay(1000 + Math.random() * 2000);
  const lowerText = text.toLowerCase();
  // ... mock response logic
  */
  
  // Uncomment this section for real API
  try {
    const response = await axios.post(`${API_BASE_URL}/assistant/ask`, {
      text: text
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });
    
    return response.data;
  } catch (error) {
    // ... error handling
  }
};
```

#### 2. Backend API Requirements

Your backend should provide:

**Endpoint:** `POST http://127.0.0.1:8000/assistant/ask`

**Request Body:**
```json
{
  "text": "What should I pack for a 5-day trip to Paris in winter?"
}
```

**Response Format:**
```json
{
  "response": "For a 5-day winter trip to Paris, I recommend packing:\n\n**Essentials:**\n• Warm coat (preferably wool or down)\n• Layered clothing..."
}
```

#### 3. Environment Configuration

For production, update the API URL in `lib/api.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
```

#### 4. CORS Configuration

Ensure your backend allows CORS requests from the frontend:

```python
# Example for FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎨 UI Features

### Smart Message Formatting
- **Bold text** (wrapped in `**text**`) displays as headers
- **Bullet points** (starting with `•`) display as formatted lists
- **Line breaks** are preserved for better readability

### Interactive Elements
- **Quick Questions**: Pre-built buttons for common travel queries
- **Category Tags**: Each quick question has a category label
- **Hover Effects**: Smooth animations and visual feedback
- **Loading States**: Realistic typing indicators

### Responsive Design
- **Mobile-first**: Optimized for all screen sizes
- **Touch-friendly**: Large tap targets for mobile devices
- **Flexible Layout**: Adapts to different content lengths

## 🛠️ Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 📁 Project Structure

```
├── app/
│   ├── globals.css          # Global styles and Tailwind imports
│   ├── layout.tsx           # Root layout component
│   └── page.tsx             # Main chat interface
├── lib/
│   └── api.ts               # API integration and mock data
├── package.json             # Dependencies and scripts
├── tailwind.config.js       # Tailwind CSS configuration
└── README.md               # This file
```

## 🎯 Mock Response Categories

The demo includes realistic responses for:

- **Packing Lists**: Winter clothing, fancy dinner attire, travel essentials
- **Attractions**: Must-see sights, hidden gems, local recommendations
- **Destinations**: Romantic getaways, budget options, luxury travel
- **Weather**: Seasonal advice, packing recommendations
- **Budget**: Cost breakdowns, money-saving tips

## 🔧 Customization

### Adding New Mock Responses

Edit `lib/api.ts` and add new responses to the `mockResponses` object:

```typescript
const mockResponses: { [key: string]: string } = {
  "your-key": "Your response text here...",
  // ... existing responses
};
```

### Styling Changes

The app uses Tailwind CSS. Key files:
- `app/globals.css` - Global styles and custom classes
- `tailwind.config.js` - Theme configuration and custom colors

### Adding New Quick Questions

Edit the `quickQuestions` array in `app/page.tsx`:

```typescript
const quickQuestions = [
  { 
    text: "Your question here", 
    icon: YourIcon, 
    category: "Category" 
  },
  // ... existing questions
];
```

## 🚀 Deployment

### Vercel (Recommended)
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Set environment variables if needed
4. Deploy!

### Other Platforms
- **Netlify**: Works with static export
- **Docker**: Use the included Dockerfile
- **Traditional hosting**: Build and serve the `out` folder

## 📝 License

MIT License - feel free to use this project for your own travel assistant applications!
