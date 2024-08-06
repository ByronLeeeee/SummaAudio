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
    os.environ["MODELSCOPE_MODULES_CACHE"] = get_MODELSCOPE_config()[
        "MODELSCOPE_MODULES_CACHE"]

    output_path = get_MODELSCOPE_config()["output_dir"]

    inference_pipeline = pipeline(
        task=Tasks.auto_speech_recognition,
        model=model,
        model_revision=model_revision,
        vad_model=vad_model, vad_model_revision=vad_model_revision,
        punc_model=punc_model, punc_model_revision=punc_model_revision,
        output_dir=output_path,
    )
    rec_result = inference_pipeline(audio_in, batch_size_s=300, batch_size_token_threshold_s=40)
    
    return rec_result

def organise_recognition(result: list):
    result_info:dict = result[0]
    full_text = result_info.get(['text'],"")
    sentence_info = result_info.get(['sentence_info'],"")
    organise_text = ''
    if sentence_info != "":
        for i in range(len(sentence_info)):
            organise_text += f"说话人{str(sentence_info[i]['spk'] + 1)}: {sentence_info[i]['text']}\n"
    return full_text, organise_text
