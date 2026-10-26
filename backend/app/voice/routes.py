from io import BytesIO
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
import speech_recognition as sr
from gtts import gTTS
from backend.app.auth.deps import current_user
from backend.app.db.models import User

router=APIRouter(prefix='/voice',tags=['voice'])
CODES={'Auto':'en-IN','English':'en-IN','Kannada':'kn-IN','Hindi':'hi-IN','Telugu':'te-IN'}
TTS={'Auto':'en','English':'en','Kannada':'kn','Hindi':'hi','Telugu':'te'}

@router.post('/transcribe')
def transcribe(file:UploadFile=File(...),language:str='Auto',user:User=Depends(current_user)):
    try:
        audio=sr.AudioFile(file.file)
        with audio as src: data=sr.Recognizer().record(src)
        text=sr.Recognizer().recognize_google(data,language=CODES.get(language,'en-IN'))
        return {'text':text}
    except sr.UnknownValueError: raise HTTPException(422,'Speech could not be understood.')
    except Exception as e: raise HTTPException(502,f'Speech recognition failed: {type(e).__name__}')

@router.post('/speak')
def speak(body:dict,user:User=Depends(current_user)):
    text=str(body.get('text','')).strip(); language=str(body.get('language','English'))
    if not text: raise HTTPException(400,'Text is required.')
    try:
        out=BytesIO(); gTTS(text=text[:4000],lang=TTS.get(language,'en')).write_to_fp(out)
        return Response(out.getvalue(),media_type='audio/mpeg')
    except Exception as e: raise HTTPException(502,f'Speech synthesis failed: {type(e).__name__}')
