from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.auth.deps import current_user
from backend.app.browser.schemas import BrowserActionRequest, OpenUrlRequest, YouTubeRequest
from backend.app.browser.service import media_action, open_url, play_youtube, search_web

router = APIRouter(prefix="/browser", tags=["browser"])

def run_safely(fn, *args):
    try:
        return fn(*args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Browser automation failed safely.") from exc

@router.post("/open")
def browser_open(body: OpenUrlRequest, _=Depends(current_user)):
    return run_safely(open_url, str(body.url))

@router.post("/search")
def browser_search(q: str = Query(min_length=1, max_length=200), _=Depends(current_user)):
    return run_safely(search_web, q)

@router.post("/youtube/play")
def youtube_play(body: YouTubeRequest, _=Depends(current_user)):
    return run_safely(play_youtube, body.query)

@router.post("/media")
def browser_media(body: BrowserActionRequest, _=Depends(current_user)):
    return run_safely(media_action, body.action)
