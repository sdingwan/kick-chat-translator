import requests

CHANNEL_INFO_URL = "https://kick.com/api/v2/channels/{slug}"

def main():
    channel_slug = input("Enter Kick channel name (slug): ").strip()
    if not channel_slug:
        print("No channel name entered.")
        return
    url = CHANNEL_INFO_URL.format(slug=channel_slug)
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible)",
        "Accept": "application/json",
        "Referer": "https://kick.com/",
        "Origin": "https://kick.com"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 403:
            print("Access forbidden or blocked by security policy. Try running this script from your local machine.")
            return
        elif resp.status_code == 404:
            print(f"Channel '{channel_slug}' not found.")
            return
        resp.raise_for_status()
        data = resp.json()
        chatroom_id = data.get("chatroom", {}).get("id")
        broadcaster_id = data.get("user", {}).get("id")
        if chatroom_id and broadcaster_id:
            print(f"\nChannel: {channel_slug}")
            print(f"Chatroom ID: {chatroom_id}")
            print(f"Broadcaster/User ID: {broadcaster_id}")
        else:
            print("Could not find chatroom or broadcaster ID in API response.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 