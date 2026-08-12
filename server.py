from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests

app = FastAPI()

# This tells the server to allow requests from your HTML app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Server is awake and running!"}

@app.get("/stream")
def stream_song(query: str):
    """
    Takes a search query, finds the top YouTube result,
    extracts the raw audio stream, and pipes it to the app.
    """
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best', 
        'noplaylist': True,
        'quiet': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 'ytsearch1:' grabs only the top 1 search result
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            
            if 'entries' not in info or len(info['entries']) == 0:
                raise HTTPException(status_code=404, detail="Song not found")
                
            # The hidden audio CDN URL
            audio_url = info['entries'][0]['url']
            
            # Stream the audio chunk-by-chunk for zero lag
            def stream_generator():
                with requests.get(audio_url, stream=True) as response:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

            return StreamingResponse(stream_generator(), media_type="audio/mp4")

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stream")
      
