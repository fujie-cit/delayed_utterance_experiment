import pyaudio
import yaml
import numpy as np
import queue
import traceback

import audio_device_util
from wave_file_recorder import WaveFileRecorder
    
def _get_current_datetime():
    """現在の日時を取得する"""
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d%H%M%S")

def main():
    # 設定ファイルを読み込む
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    audio_config = config["AUDIO DEVICE CONFIG"]
    delay_config = config["DELAY CONFIG"]
    recording_config = config["RECORDING CONFIG"]

    input_device_name = audio_config["INPUT DEVICE NAME"]
    output_device_name = audio_config["OUTPUT DEVICE NAME"]
    input_channels = audio_config["INPUT CHANNELS"]
    output_channels = audio_config["OUTPUT CHANNELS"]
    sample_rate = audio_config["SAMPLE RATE"]
    sample_width = audio_config["SAMPLE WIDTH"]
    block_size = audio_config["BLOCK SIZE"]

    target_channel = delay_config["TARGET CHANNEL"]
    delay_in_sec = delay_config["DELAY IN SECONDS"]

    user_channel = recording_config["USER CHANNEL"]
    output_dir = recording_config["OUTPUT DIR"]

    # 録音ファイル名を生成する
    # 0づめして遅延量をミリ秒単位の文字列に変換する
    delay_in_msec_str = f"{int(delay_in_sec*1000):06d}"
    # 録音ファイル名を生成する
    wav_filename = f"{recording_config['OUTPUT DIR']}/{_get_current_datetime()}_{delay_in_msec_str}.wav"

    # 録音ファイル名を表示して開始を確認する
    print(f"*** filename is {wav_filename} ***")
    input("Press Enter to start recording...")

    # 入力デバイスのインデクスを取得
    input_device_index, _ = audio_device_util.get_audio_device_index(input_device_name)
    if input_device_index == -1:
        raise Exception(f"Input device ({input_device_name}) not found.")
    
    # 出力デバイスのインデクスを取得
    output_device_index, _ = audio_device_util.get_audio_device_index(output_device_name)
    if output_device_index == -1:
        raise Exception(f"Output device ({output_device_name}) not found.")

    # 遅延処理用キューの作成
    frames_for_playback = queue.Queue()
    for i in range(0, int(delay_in_sec * sample_rate / block_size)):
        frames_for_playback.put(b'\x00' * block_size * sample_width)
        
    p = pyaudio.PyAudio()
    try:
        in_stream = p.open(input_device_index=input_device_index,
                        channels=input_channels,
                        format=p.get_format_from_width(sample_width),
                        rate=sample_rate,
                        input=True,
                        output=False,
                        frames_per_buffer=block_size)
        out_stream = p.open(output_device_index=output_device_index,
                        channels=output_channels,
                        format=p.get_format_from_width(sample_width),
                        rate=sample_rate,
                        input=False,
                        output=True,
                        frames_per_buffer=block_size)
    except IOError as e:
        print(f"An IOError occurred: {e}")
        print("Here is the traceback:")
        traceback.print_exc()
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print("Here is the traceback:")
        traceback.print_exc()
        return

    # 録音開始
    recorder = WaveFileRecorder()
    recorder.start(wav_filename,
                   channels=3, # ユーザ音声, システム音声(遅延あり), システム音声(遅延なし)
                   sample_width=sample_width, sample_rate=sample_rate)
    
    try:
        while True:
            # 録音データの受け取り
            in_data = in_stream.read(block_size, exception_on_overflow=False)

            # マルチチャネルデータにする
            in_data_np = np.frombuffer(in_data, dtype=np.int16).reshape(-1, input_channels)
                
            # ユーザ音声を取り出す
            user_data_np = in_data_np[:, user_channel]
            # ターゲット音声を取り出す
            target_data_np = in_data_np[:, target_channel]
            # キューにターゲット音声を入れる
            frames_for_playback.put(target_data_np.tobytes())
            # 遅延処理済データを取り出す
            playback_data = frames_for_playback.get()
            # 遅延処理済データをnumpyに変換する
            playback_data_np = np.frombuffer(playback_data, dtype=np.int16)
            
            # 再生する
            out_stream.write(playback_data)

            # 録音データを保存する
            rec_data_np = np.vstack([user_data_np, playback_data_np, target_data_np]).T
            recorder.put(rec_data_np.tobytes())
                         
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        print("Finished recording and playback")

        in_stream.stop_stream()
        out_stream.stop_stream()

        in_stream.close()
        out_stream.close()

        p.terminate()

        recorder.terminate()

if __name__ == "__main__":
    main()
