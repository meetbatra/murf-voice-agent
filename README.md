# Murf Voice Agent - LiveKit Edition

A real-time AI voice agent powered by **Murf Falcon TTS**, **Google Gemini 2.5 Flash**, and **Deepgram Nova-3 STT**, built on the LiveKit platform.

## About This Project

This voice agent application demonstrates ultra-fast, high-quality conversational AI using cutting-edge technologies:

- **Murf Falcon TTS** - Industry-leading text-to-speech with ~360ms TTFB
- **Google Gemini 2.5 Flash** - Advanced large language model for natural conversations
- **Deepgram Nova-3** - High-accuracy speech-to-text transcription
- **LiveKit** - Real-time communication infrastructure with turn detection and noise cancellation

### Features

- Real-time voice interaction with minimal latency
- Contextually-aware turn detection
- Background noise cancellation
- Beautiful, responsive UI with theme support
- Production-ready deployment configuration

## Repository Structure

This is a **monorepo** that contains both the backend and frontend for building voice agent applications. It's designed to be your starting point for each day's challenge task.

```
murf-voice-agent/
├── backend/          # Python backend with LiveKit Agents + Murf Falcon TTS
├── frontend/         # Next.js 15 + React 19 frontend with LiveKit components
├── start_app.sh      # Convenience script to start all services
└── README.md         # This file
```

### Backend

Python-based voice agent backend using LiveKit Agents framework with integrated AI services.

**Tech Stack:**

- **Framework**: LiveKit Agents v1.3.2
- **TTS**: Murf Falcon (voice: en-US-matthew, style: Conversation)
- **LLM**: Google Gemini 2.5 Flash
- **STT**: Deepgram Nova-3
- **Additional**: Silero VAD, LiveKit Turn Detector, Noise Cancellation
- **Package Manager**: uv (fast Python package installer)

**Key Features:**

- Preemptive speech generation for reduced latency
- Context-aware turn detection
- Real-time transcription with metrics logging
- Background voice cancellation
- Production-ready with Docker support

[→ Backend Documentation](./backend/README.md)

### Frontend

Modern Next.js frontend with LiveKit React components for seamless voice interaction.

**Tech Stack:**

- **Framework**: Next.js 15.5.2 with Turbopack
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4 with custom theme
- **Components**: LiveKit React Components
- **Package Manager**: pnpm

**Key Features:**

- Real-time voice chat with visual feedback
- Dark/light theme support with orange accent colors
- Audio visualization and device controls
- Chat transcript display
- Responsive, modern UI design

[→ Frontend Documentation](./frontend/README.md)

## Quick Start

### Prerequisites

Make sure you have the following installed:

- **Python 3.9+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with [pnpm](https://pnpm.io/installation)
- **LiveKit Server** (for local development)
  ```bash
  brew install livekit
  ```
- **LiveKit Cloud Account** (recommended for production)
  - Sign up at [LiveKit Cloud](https://cloud.livekit.io/)
  - Region: India South

### Required API Keys

You'll need API keys from the following services:

1. **LiveKit Cloud** - Get your credentials from [LiveKit Cloud Dashboard](https://cloud.livekit.io/)
2. **Murf AI** - Get API key from [Murf API Dashboard](https://murf.ai/api)
3. **Google AI Studio** - Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
4. **Deepgram** - Get API key from [Deepgram Console](https://console.deepgram.com/)

### 1. Clone the Repository

```bash
git clone https://github.com/murf-ai/ten-days-of-voice-agents-2025.git
cd murf-voice-agent
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies using uv
uv sync

# Create environment file
cp .env.example .env.local

# Edit .env.local with your credentials:
nano .env.local
```

Add the following to `.env.local`:

```bash
# LiveKit Cloud Credentials
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# AI Service API Keys
GOOGLE_API_KEY=your_google_api_key
MURF_API_KEY=your_murf_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
```

```bash
# Download required models (Silero VAD, turn detector)
uv run python src/agent.py download-files
```

**Note:** You can also use LiveKit CLI to auto-populate credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies using pnpm
pnpm install

# Create environment file
cp .env.example .env.local

# Edit .env.local with the same LiveKit credentials
nano .env.local
```

Add the following to `.env.local`:

```bash
# LiveKit Cloud Credentials (same as backend)
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Optional (for production deployments)
CONFIG_ENDPOINT=
SANDBOX_ID=
```

### 4. Run the Application

#### Option A: Use the convenience script (recommended)

The easiest way to start all services at once:

```bash
# From the root directory
chmod +x start_app.sh
./start_app.sh
```

This single command will start:
1. **LiveKit Server** (local development server on port 7880)
2. **Backend Agent** (Python agent listening for LiveKit connections)
3. **Frontend App** (Next.js app at http://localhost:3000)

#### Option B: Run services individually

If you prefer to run services in separate terminals:

```bash
# Terminal 1 - LiveKit Server
livekit-server --dev

# Terminal 2 - Backend Agent
cd backend
uv run python src/agent.py dev

# Terminal 3 - Frontend
cd frontend
pnpm dev
```

### 5. Test Your Voice Agent

1. Open your browser and navigate to **http://localhost:3000**
2. Click the **"START CALL"** button (orange button)
3. Allow microphone permissions when prompted
4. Start talking to your AI voice agent!

The agent will:
- Listen to your speech (Deepgram Nova-3)
- Process your query (Google Gemini 2.5 Flash)
- Respond with natural voice (Murf Falcon TTS)

### Troubleshooting

**Issue: Frontend shows "Agent is listening" but doesn't respond**
- Ensure backend and frontend are using the same LiveKit credentials
- Check that all three services (LiveKit server, backend, frontend) are running

**Issue: "Permission denied" when running start_app.sh**
```bash
chmod +x start_app.sh
```

**Issue: Port already in use**
- LiveKit Server uses port 7880, 7881, 7882
- Frontend uses port 3000
- Kill any conflicting processes or change ports in configuration

**Issue: Button showing wrong color**
- Clear browser cache and hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows/Linux)
- Tailwind CSS 4 requires proper CSS compilation

## Architecture

### Connection Flow

```
User Browser (Frontend)
        ↓
LiveKit Cloud Instance (wss://voice-agent-t5jxr54l.livekit.cloud)
        ↑
Python Backend (Agent)
```

Both frontend and backend connect to the same LiveKit Cloud instance. The agent:
1. Registers with LiveKit Cloud and waits for job requests
2. When a user starts a call, LiveKit dispatches a job to the agent
3. Agent processes audio using Deepgram STT → Gemini LLM → Murf Falcon TTS
4. LiveKit handles real-time audio streaming between user and agent

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Next.js 15 + React 19 | Modern web UI |
| **Backend** | Python + LiveKit Agents | Voice agent logic |
| **TTS** | Murf Falcon | Text-to-speech (~360ms TTFB) |
| **LLM** | Google Gemini 2.5 Flash | Conversation intelligence |
| **STT** | Deepgram Nova-3 | Speech-to-text transcription |
| **Infrastructure** | LiveKit Cloud | Real-time communication |
| **Styling** | Tailwind CSS 4 | UI theming |
| **Package Managers** | uv (Python) + pnpm (Node) | Fast dependency management |

## Customization

### Modify Voice Agent Behavior

Edit `backend/src/agent.py` to customize:

- **Voice style**: Change `voice="en-US-matthew"` or `style="Conversation"`
- **LLM model**: Switch from Gemini to other supported models
- **System prompt**: Modify agent personality and instructions
- **Turn detection**: Adjust turn detection sensitivity

### Customize UI Theme

Edit `frontend/styles/globals.css` to change colors:

```css
:root {
  --primary: oklch(0.5553 0.1455 48.9975); /* Orange accent */
  --background: oklch(0.9885 0.0057 84.5659); /* Light background */
  /* ... more color variables */
}
```

The app uses Tailwind CSS 4's `@theme inline` directive for theming.

## Performance Metrics

Based on actual logs from this implementation:

| Metric | Value |
|--------|-------|
| **TTS TTFB** | ~360-380ms (Murf Falcon) |
| **LLM TTFT** | ~1.3-2.3s (Gemini 2.5 Flash) |
| **STT Latency** | Real-time streaming (Deepgram) |
| **EOU Detection** | 0-1.2s (LiveKit Turn Detector) |
| **Tokens/Second** | 10-23 tokens/s (Gemini) |

## Development Tips

1. **Use LiveKit Cloud for production** - More reliable than self-hosted server
2. **Monitor logs** - Backend logs show detailed metrics for each interaction
3. **Test with different voices** - Murf Falcon supports multiple voices and styles
4. **Optimize prompts** - Shorter, clearer prompts reduce LLM latency
5. **Enable caching** - Use prompt caching for repeated system instructions

## Documentation & Resources

### Official Documentation

- [Murf Falcon TTS API](https://murf.ai/api/docs/text-to-speech/streaming) - Ultra-fast TTS documentation
- [LiveKit Agents](https://docs.livekit.io/agents) - Voice agent framework
- [Google Gemini API](https://ai.google.dev/gemini-api/docs) - LLM integration
- [Deepgram Nova-3](https://developers.deepgram.com/) - STT transcription

### Templates & Examples

- [LiveKit Agent Starter (Python)](https://github.com/livekit-examples/agent-starter-python)
- [LiveKit Agent Starter (React)](https://github.com/livekit-examples/agent-starter-react)
- [Murf Voice Agent Challenges](./challenges/) - Daily challenge tasks

### Community

- [LiveKit Community Slack](https://livekit.io/join-slack)
- [Murf AI Discord](https://murf.ai/discord)
- [GitHub Discussions](https://github.com/murf-ai/ten-days-of-voice-agents-2025/discussions)

## Testing

### Backend Tests

The backend includes a comprehensive test suite for voice agent functionality:

```bash
cd backend
uv run pytest
```

Learn more in the [LiveKit testing documentation](https://docs.livekit.io/agents/build/testing/).

### Manual Testing

1. Start all services using `./start_app.sh`
2. Open browser DevTools (F12) to monitor network and console
3. Test different conversation scenarios
4. Check backend terminal for detailed metrics logs

## Deployment

### Deploy to Production

For production deployment:

1. **Backend**: Use Docker to deploy Python agent
   ```bash
   cd backend
   docker build -t voice-agent-backend .
   docker run -e LIVEKIT_URL=... -e MURF_API_KEY=... voice-agent-backend
   ```

2. **Frontend**: Deploy to Vercel, Netlify, or similar
   ```bash
   cd frontend
   pnpm build
   # Deploy the .next folder
   ```

3. **LiveKit**: Use LiveKit Cloud (already configured in this setup)

### Environment Variables for Production

Ensure all environment variables are set in your deployment platform:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- `MURF_API_KEY`, `GOOGLE_API_KEY`, `DEEPGRAM_API_KEY`

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:

- Bug fixes
- Feature enhancements
- Documentation improvements
- Performance optimizations

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is based on MIT-licensed templates from LiveKit. See individual LICENSE files in backend and frontend directories for details.

## Acknowledgments

Built with amazing technologies:

- **Murf AI** - For the incredible Falcon TTS API
- **LiveKit** - For the robust real-time communication platform
- **Google** - For Gemini 2.5 Flash LLM
- **Deepgram** - For Nova-3 STT transcription

---

**Built for the AI Voice Agents Challenge by [murf.ai](https://murf.ai)**

Happy coding! 🎙️🤖
