import pyaudio
import difflib

def get_audio_device_list():
    """音声の入出力デバイスのリストを作成する
    
    Returns:
        list: デバイスのリスト
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    input_devices = []
    output_devices = []

    for i in range(0, numdevices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        device_name = device_info.get('name')
        device_max_input_channels = device_info.get('maxInputChannels')
        device_max_output_channels = device_info.get('maxOutputChannels')

        if device_max_input_channels > 0:
            input_devices.append([device_name, i])
        if device_max_output_channels > 0:
            output_devices.append([device_name, i])
    
    return input_devices, output_devices


def get_audio_device_index(device_name, cutoff=0.2):
    """指定したデバイス名に最も近いデバイスのインデックスを返す
    
    Args:
        device_name (str): デバイス名
        cutoff (float, optional): 類似度の閾値. Defaults to 0.2.
    
    Returns:
        int: デバイスのインデックス. 見つからない場合は-1
        str: デバイス名. 見つからない場合はNone                
    """
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    
    device_names = []
    for i in range(0, numdevices):
        device_names.append(p.get_device_info_by_host_api_device_index(0, i).get('name'))
    
    # 最も近い名前のデバイスを探す
    closest_matches = difflib.get_close_matches(device_name, device_names, n=1, cutoff=cutoff)
    
    if closest_matches:
        closest_match = closest_matches[0]
        return device_names.index(closest_match), closest_match
    else:
        return -1, None

if __name__ == "__main__":
    import sys
    
    device_index, device_name = get_audio_device_index(sys.argv[1])
    if device_index != -1:
        print(f"The closest match is at index {device_index} ({device_name})")
    else:
        print("No close match found.")

    print("----")
    input_devices, output_devices = get_audio_device_list()
    print("Input devices:")
    for device in input_devices:
        print(f"    {device[0]} ({device[1]})")
    print("Output devices:")
    for device in output_devices:
        print(f"    {device[0]} ({device[1]})")
