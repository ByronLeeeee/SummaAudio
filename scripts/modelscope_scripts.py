from modelscope.utils.constant import Tasks
from modelscope.pipelines import pipeline
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.utils import load_config

def get_MODELSCOPE_config():
    return load_config('MODELSCOPE')


def recognition(audio_in, model, model_revision, vad_model, vad_model_revision, punc_model, punc_model_revision) -> list:
    os.environ["MODELSCOPE_CACHE"] = get_MODELSCOPE_config()[
        "MODELSCOPE_CACHE"]

    output_path = get_MODELSCOPE_config()["output_dir"]

    inference_pipeline = pipeline(
        task=Tasks.auto_speech_recognition,
        model=model,
        model_revision=model_revision,
        vad_model=vad_model, vad_model_revision=vad_model_revision,
        punc_model=punc_model, punc_model_revision=punc_model_revision,
        output_dir=output_path,
    )
    rec_result = inference_pipeline(audio_in)
    
    return rec_result

def organise_recognition(result: list):
    if not result or not isinstance(result[0], dict):
        raise ValueError("Invalid input format: 'result' should be a non-empty list with dictionaries as elements.")
    
    result_info = result[0]
    full_text = result_info.get('text', "")
    sentence_info = result_info.get('sentence_info', "")
    
    organise_text = ""
    if sentence_info and isinstance(sentence_info, list):
        current_speaker = None
        current_text = ""
        
        for item in sentence_info:
            if current_speaker is None or item['spk'] != current_speaker:
                if current_speaker is not None:
                    organise_text += f"说话人{str(current_speaker + 1)}: {current_text}\n\n"
                current_speaker = item['spk']
                current_text = item['text']
            else:
                current_text += "" + item['text']
        
        if current_speaker is not None:
            organise_text += f"说话人{str(current_speaker + 1)}: {current_text}"
    
    return full_text, organise_text
