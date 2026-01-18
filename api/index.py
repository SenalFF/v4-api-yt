import subprocess
import sys
import importlib
import json
import re
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        importlib.import_module(import_name)

# Auto-install requirements
install_and_import("fastapi")
install_and_import("uvicorn")
install_and_import("yt-dlp", "yt_dlp")
install_and_import("youtube-search", "youtube_search")

import yt_dlp
from youtube_search import YoutubeSearch

def setup_cookies():
    # Netscape cookies MUST be tab-separated (\t)
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

setup_cookies()

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
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'cookiefile': '/tmp/yt-dlp/cookies.txt',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
        },
        'youtube_include_dash_manifest': True,
        'youtube_include_hls_manifest': True,
        'socket_timeout': 60,
        'retries': 5,
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
                "version": "v4-Lite",
                "title": video.get("title"),
                "uploader": video.get("channel"),
                "upload_date": video.get("publish_time"),
                "views": video.get("views"),
                "likes": "N/A",
                "url": video_url
            }
        else:
            ydl_opts = get_base_ydl_opts()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(input_str, download=False)
                return {
                    "status": True,
                    "creator": "mr senal",
                    "version": "v4-Lite",
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
    ydl_opts.update({
        'extract_flat': False,
        'merge_output_format': 'mp4',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'ignoreerrors': True,
    })
    
    if quality:
        ydl_opts['format'] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
    else:
        ydl_opts['format'] = "bv*+ba/b"
    
    ydl_opts['merge_output_format'] = 'mp4'
    
    if not (input_str.startswith("http://") or input_str.startswith("https://")):
        input_str = f"ytsearch1:{input_str}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_str, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            audio_formats = []
            video_formats = []
            
            for f in info.get('formats', []):
                url = f.get("url")
                if not url or "manifest" in url or "m3u8" in url or "googlevideo.com/api/manifest" in url:
                    continue
                
                vcodec = f.get('vcodec')
                acodec = f.get('acodec')
                abr = f.get('abr') or 0
                height = f.get('height') or 0
                
                # Format resolution as height + p (e.g. 720p)
                res_label = f"{height}p" if height > 0 else (f.get("resolution") or "N/A")
                
                format_data = {
                    "resolution": res_label,
                    "audio_bitrate": f"{abr}kbps" if abr > 0 else "N/A",
                    "file_extension": f.get("ext"),
                    "video_codec": vcodec,
                    "audio_codec": acodec,
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "direct_download_url": url
                }
                
                if vcodec == 'none' and acodec != 'none':
                    if 48 <= abr <= 512:
                        # Map audio to common names
                        ext = f.get("ext", "")
                        if "mp4" in ext or "m4a" in ext:
                            format_data["format"] = "mpa"
                        elif "opus" in acodec:
                            format_data["format"] = "opus"
                        else:
                            format_data["format"] = "mp3"
                        
                        # Add quality note based on bitrate
                        if abr >= 256:
                            format_data["quality"] = "highest"
                        elif abr >= 128:
                            format_data["quality"] = "medium"
                        else:
                            format_data["quality"] = "low"
                            
                        audio_formats.append(format_data)
                elif vcodec != 'none' and acodec != 'none':
                    if 144 <= height <= 1080:
                        video_formats.append(format_data)

            return {
                "status": True,
                "creator": "mr senal",
                "version": "v4-Lite",
                "title": info.get("title"),
                "audio": audio_formats,
                "video": video_formats
            }
    except Exception as e:
        return {"status": False, "error": str(e)}

def extract_all_formats(input_str: str):
    ydl_opts = get_base_ydl_opts()
    if not (input_str.startswith("http://") or input_str.startswith("https://")):
        input_str = f"ytsearch1:{input_str}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(input_str, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            
            formats = []
            for f in info.get('formats', []):
                url = f.get("url")
                if not url or "googlevideo.com/api/manifest" in url:
                    continue
                    
                height = f.get('height') or 0
                res_label = f"{height}p" if height > 0 else (f.get("resolution") or "N/A")
                
                formats.append({
                    "resolution": res_label,
                    "fps": f.get("fps"),
                    "filesize": f.get("filesize") or f.get("filesize_approx"),
                    "vcodec": f.get("vcodec"),
                    "acodec": f.get("acodec"),
                    "abr": f.get("abr"),
                    "vbr": f.get("vbr"),
                    "format_note": f.get("format_note"),
                    "url": url
                })

            return {
                "status": True,
                "creator": "mr senal",
                "version": "v4-Lite",
                "title": info.get("title"),
                "total_formats": len(formats),
                "formats": formats
            }
    except Exception as e:
        return {"status": False, "error": str(e)}

@app.get("/")
async def root_endpoint():
    return {
        "status": True,
        "creator": "mr senal",
        "version": "v4-Lite",
        "message": "Welcome to Senal YouTube Extractor API 🚀",
        "available_qualities": {
            "video": ["144p", "240p", "360p", "480p", "720p", "1080p"],
            "audio": ["mp3", "mpa", "opus", "quality: low/medium/highest"]
        },
        "endpoints": {
            "search": {
                "url": "/search?q=video+title",
                "example": "/search?q=alan+walker+faded"
            },
            "download": {
                "url": "/download?url=VIDEO_URL&quality=720p or mp3",
                "example": "/download?url=https://www.youtube.com/watch?v=60ItHLz5WEA&quality=720p"
            },
            "formats": {
                "url": "/formats?url=VIDEO_URL",
                "example": "/formats?url=https://www.youtube.com/watch?v=60ItHLz5WEA"
            }
        }
    }

@app.get("/search")
async def search_endpoint(url: Optional[str] = None, q: Optional[str] = None):
    target = url or q
    if not target:
        return await root_endpoint()
    return extract_search_info(target)

@app.get("/formats")
async def formats_endpoint(url: Optional[str] = None, q: Optional[str] = None):
    target = url or q
    if not target:
        return {"status": False, "error": "URL or query parameter 'q' is required"}
    return extract_all_formats(target)

@app.get("/download")
async def download_endpoint(url: Optional[str] = None, q: Optional[str] = None, quality: Optional[str] = Query(None, description="Target height (e.g., 240, 360, 480)")):
    target = url or q
    if not target:
        return {
            "status": False, 
            "error": "URL or query parameter 'q' is required",
            "usage": {
                "search": "/search?q=query or /search?url=url",
                "formats": "/formats?url=url"
            }
        }
    
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
        return {"status": False, "error": "URL or query is required"}
    return extract_search_info(target)

@app.post("/download")
async def post_download(request: SearchRequest, quality: Optional[str] = None):
    target = request.url or request.query
    if not target:
        return {"status": False, "error": "URL or query is required"}
    
    q_val = None
    if quality:
        match = re.search(r'(\d+)', str(quality))
        if match:
            q_val = int(match.group(1))
            
    return extract_download_info(target, q_val)

@app.post("/formats")
async def post_formats(request: SearchRequest):
    target = request.url or request.query
    if not target:
        return {"status": False, "error": "URL or query is required"}
    return extract_all_formats(target)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
