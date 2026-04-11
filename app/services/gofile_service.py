import requests

def get_best_server():
    try:
        response = requests.get('https://api.gofile.io/servers')
        data = response.json()
        if data['status'] == 'ok' and data['data']['servers']:
            return data['data']['servers'][0]['name']
    except Exception as e:
        print(f"Error getting GoFile server: {e}")
    return None

def upload_to_gofile(file_path):
    server = get_best_server()
    if not server:
        return None
    
    url = f'https://{server}.gofile.io/uploadFile'
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)
            data = response.json()
            if data['status'] == 'ok':
                return data['data']['downloadPage'] # URL to see/download the file
    except Exception as e:
        print(f"Error uploading to GoFile: {e}")
    return None
