import os
import json
import re
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import yt_dlp
from youtube_search import YoutubeSearch

def setup_cookies():
    default_cookies = (
        "# Netscape HTTP Cookie File\n"
        "# https://curl.haxx.se/rfc/cookie_spec.html\n"
        "# This is a generated file! Do not edit.\n\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1802746903\t__Secure-3PAPISID\tbQ8MoLrNbRSshP9O/A7OPhHZftwwN7N-V8\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1797669119\tLOGIN_INFO\tAFmmF2swRQIgX1HYbzoBnkHKYwIlChEo1PxMCqTiPMcSdR0vwFpDdAwCIQC7UZzE0yU5jVdaDqW75EX9r3b96ro8kB5bdFQGf4-rUQ:QUQ3MjNmeVRiRjhwOEpoWXh1TExHdlNFTi1hM0VWeDRiSUI1eHQ2b0kxNXdJLXUwS09lTlYtY21CQndPTTJZODJZUlMtaS0yNnpJU1VNVEgzTXQxbXVIbGYwYVZDcHNFb3pVcjRfYzR0WnU2ZnFVUW1pdVBwMXE4aEVtSUdzR2hsT2FkdzR3bFdSNzFvNmJyaE1od2lYVEdRcjVjZzF4RG5B\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1802746903\t__Secure-3PSID\tg.a0005ggEUbHTHhLk3prGZ7Wp2POHRKhKYWwnMMDL1NTe1icbH0Jy40KLJZRs9-lXBgYwlwjyzQACgYKAVQSARMSFQHGX2MiUdi2tNuXG56KF1mXB2tDQhoVAUF8yKpLXIltX4gD018IjmO8GnxD0076\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1803239253\tPREF\ttz=Asia.Colombo&f7=100&f6=40000000\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1800215257\t__Secure-1PSIDTS\tsidts-CjQB7I_69P5xCw71hr2Z3E90gFLniSyVWxZgxf3QBd_w_msTbPwIzTzB2H0OGd9wPYlBlo28EAA\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1800215257\t__Secure-3PSIDTS\tsidts-CjQB7I_69P5xCw71hr2Z3E90gFLniSyVWxZgxf3QBd_w_msTbPwIzTzB2H0OGd9wPYlBlo28EAA\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1800215296\t__Secure-3PSIDCC\tAKEyXzUEz5H_7cE4SM1X31VuAmEIwlSaP2OounSM1Osj-FSqVqxexRlWg_ctk6Gz8cS21sCuf3A\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1784231249\tVISITOR_INFO1_LIVE\tPtS166wesDk\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1784231249\tVISITOR_PRIVACY_METADATA\tCgJMSxIEGgAgFQ%3D%3D\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1784227324\t__Secure-YNID\t15.YT=QPG91qjjN8kGqlefUNesPdldOxeFbp04BruLivqTDOC8zlgGKpdHRE84JFYdhL4tzLAq53nrNS_FBvFJy_zPt3_R0CfOQ6um_h0fIkqc6KHm_NIkrhbKJfvWbN_aQPwH1HY3GH1jQhIWn5Ku0T12c3LsXaKbt7uIMGB2ntqu07zyr-XqBt75l-QPwgOTk-6yRS7GJ-fXNt5pMtv_oeKZnZux4gJhrc6pmNZCiHFC0EOrtmJ_pCSF0q0d8cylWxy6z-Un7XwGhZVtg1V_Rc72aScO-3LFREabTjjhkZoqEt52PiykyAaZ6k5Ha9W921b3eBzYpQli4hP1n_04X4zWxg\n"
        ".youtube.com\tTRUE\t/\tTRUE\t0\tYSC\tKSAvcaBsqpY\n"
        ".youtube.com\tTRUE\t/\tTRUE\t1784227324\t__Secure-ROLLOUT_TOKEN\tCKmU7JjxnLHQhAEQ6qb1rseEjwMY0b62g52TkgM%3D\n"
    )
    cookie_content = os.environ.get("YOUTUBE_COOKIES_CONTENT", default_cookies)
    os.makedirs("/tmp/yt-dlp", exist_ok=True)
    cookies_path = "/tmp/yt-dlp/cookies.txt"
    with open(cookies_path, "w") as f:
        f.write(cookie_content)
    return cookies_path

cookies_path = setup_cookies()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    url: Optional[str] = None
    query: Optional[str] = None

def get_base_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'no_color': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'referer': 'https://www.youtube.com/',
        'cookiefile': cookies_path,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
        },
        'socket_timeout': 30,
        'retries': 3,
        'extract_flat': False,
        'format': 'best',
    }

def extract_search_info(input_str: str):
    try:
        if not (input_str.startswith("http://") or input_str.startswith("https://")):
            results = YoutubeSearch(input_str, max_results=1).to_dict()
            if not results:
                return {"status": False, "error": "No results found"}
            video = results[0]
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            return {
                "status": True,
                "creator": "mr senal",
                "version": "v4-Production",
                "title": video.get("title"),
                "uploader": video.get("channel"),
                "upload_date": video.get("publish_time"),
                "views": video.get("views"),
                "url": video_url
            }
        else:
            ydl_opts = get_base_ydl_opts()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(input_str, download=False)
                return {
                    "status": True,
                    "creator": "mr senal",
                    "version": "v4-Production",
                    "title": info.get("title"),
                    "uploader": info.get("uploader"),
                    "upload_date": info.get("upload_date"),
                    "views": info.get("view_count"),
                    "likes": info.get("like_count"),
                    "url": info.get("webpage_url")
                }
    except Exception as e:
        return {"status": False, "error": str(e)}

def extract_download_info(input_str: str, quality: Optional[int] = None):
    ydl_opts = get_base_ydl_opts()
    
    # Set format based on quality
    if quality:
        ydl_opts['format'] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best"
    else:
        ydl_opts['format'] = "bestvideo+bestaudio/best"
    
    if not (input_str.startswith("http://") or input_str.startswith("https://")):
        input_str = f"ytsearch1:{input_str}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_str, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            audio_formats = []
            video_formats = []
            
            # Get all available formats
            formats = info.get('formats', [])
            
            # Process each format
            for f in formats:
                url = f.get("url")
                if not url:
                    continue
                
                # Skip manifest/playlist URLs
                if any(x in url.lower() for x in ["manifest", "m3u8", "mpd"]):
                    continue
                
                format_id = f.get('format_id', '')
                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                ext = f.get('ext', 'mp4')
                abr = f.get('abr') or 0
                height = f.get('height') or 0
                width = f.get('width') or 0
                fps = f.get('fps')
                tbr = f.get('tbr') or 0
                filesize = f.get('filesize') or f.get('filesize_approx')
                
                # Common format data
                format_data = {
                    "format_id": format_id,
                    "ext": ext,
                    "filesize": filesize,
                    "url": url
                }
                
                # Audio-only formats
                if vcodec == 'none' and acodec != 'none':
                    if abr >= 48:  # Valid audio bitrate
                        format_data.update({
                            "type": "audio",
                            "quality": f"{int(abr)}kbps" if abr else "Unknown",
                            "codec": acodec,
                            "bitrate": int(abr) if abr else None
                        })
                        
                        # Categorize by quality
                        if abr >= 160:
                            format_data["quality_label"] = "High"
                        elif abr >= 128:
                            format_data["quality_label"] = "Medium"
                        else:
                            format_data["quality_label"] = "Low"
                        
                        audio_formats.append(format_data)
                
                # Video formats (with or without audio)
                elif vcodec != 'none':
                    if height > 0:
                        format_data.update({
                            "type": "video",
                            "quality": f"{height}p",
                            "resolution": f"{width}x{height}" if width else f"{height}p",
                            "fps": fps,
                            "vcodec": vcodec,
                            "acodec": acodec if acodec != 'none' else None,
                            "has_audio": acodec != 'none',
                            "tbr": int(tbr) if tbr else None
                        })
                        
                        video_formats.append(format_data)
            
            # Sort formats
            audio_formats.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
            video_formats.sort(key=lambda x: int(x.get('quality', '0p').replace('p', '')), reverse=True)
            
            return {
                "status": True,
                "creator": "mr senal",
                "version": "v4-Production",
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "description": info.get("description", "")[:500] if info.get("description") else None,
                "formats": {
                    "audio": audio_formats,
                    "video": video_formats
                }
            }
    except Exception as e:
        return {"status": False, "error": str(e)}

def extract_all_formats(input_str: str):
    ydl_opts = get_base_ydl_opts()
    ydl_opts['format'] = 'all'
    
    if not (input_str.startswith("http://") or input_str.startswith("https://")):
        input_str = f"ytsearch1:{input_str}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_str, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            all_formats = []
            for f in info.get('formats', []):
                url = f.get("url")
                if not url:
                    continue
                
                height = f.get('height') or 0
                
                all_formats.append({
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f"{height}p" if height > 0 else "audio",
                    "fps": f.get("fps"),
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec"),
                    "abr": f.get("abr"),
                    "vbr": f.get("vbr"),
                    "tbr": f.get("tbr"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "protocol": f.get("protocol"),
                    "url": url
                })

            return {
                "status": True,
                "creator": "mr senal",
                "version": "v4-Production",
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "total_formats": len(all_formats),
                "formats": all_formats
            }
    except Exception as e:
        return {"status": False, "error": str(e)}

@app.get("/")
async def root_endpoint():
    return {
        "status": True,
        "creator": "mr senal",
        "version": "v4-Production",
        "message": "🚀 Senal YouTube Extractor API - Production Ready",
        "features": [
            "✅ Direct download URLs",
            "✅ Multiple quality options",
            "✅ Audio extraction",
            "✅ Video + Audio formats",
            "✅ Fast & reliable"
        ],
        "endpoints": {
            "/search": "Search video info - ?q=video+title or ?url=VIDEO_URL",
            "/download": "Get download links - ?url=VIDEO_URL&quality=720",
            "/formats": "Get all available formats - ?url=VIDEO_URL"
        },
        "usage_examples": {
            "search_by_query": "/search?q=despacito",
            "search_by_url": "/search?url=https://youtu.be/VIDEO_ID",
            "download_720p": "/download?url=https://youtu.be/VIDEO_ID&quality=720",
            "download_best": "/download?url=https://youtu.be/VIDEO_ID",
            "all_formats": "/formats?url=https://youtu.be/VIDEO_ID"
        }
    }

@app.get("/search")
async def search_endpoint(url: Optional[str] = None, q: Optional[str] = None):
    target = url or q
    if not target:
        raise HTTPException(status_code=400, detail="Parameter 'url' or 'q' is required")
    return extract_search_info(target)

@app.get("/formats")
async def formats_endpoint(url: Optional[str] = None, q: Optional[str] = None):
    target = url or q
    if not target:
        raise HTTPException(status_code=400, detail="Parameter 'url' or 'q' is required")
    return extract_all_formats(target)

@app.get("/download")
async def download_endpoint(
    url: Optional[str] = None, 
    q: Optional[str] = None, 
    quality: Optional[str] = Query(None, description="Video quality: 144, 240, 360, 480, 720, 1080, 1440, 2160")
):
    target = url or q
    if not target:
        raise HTTPException(status_code=400, detail="Parameter 'url' or 'q' is required")
    
    q_val = None
    if quality:
        match = re.search(r'(\d+)', str(quality))
        if match:
            q_val = int(match.group(1))
    
    return extract_download_info(target, q_val)

@app.post("/search")
async def post_search(request: SearchRequest):
    target = request.url or request.query
    if not target:
        raise HTTPException(status_code=400, detail="Field 'url' or 'query' is required")
    return extract_search_info(target)

@app.post("/download")
async def post_download(request: SearchRequest, quality: Optional[int] = None):
    target = request.url or request.query
    if not target:
        raise HTTPException(status_code=400, detail="Field 'url' or 'query' is required")
    return extract_download_info(target, quality)

@app.post("/formats")
async def post_formats(request: SearchRequest):
    target = request.url or request.query
    if not target:
        raise HTTPException(status_code=400, detail="Field 'url' or 'query' is required")
    return extract_all_formats(target)

app_handler = app
