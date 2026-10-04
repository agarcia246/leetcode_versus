import requests


def get_leetcode_player_submissions():
    url = "https://leetcode.com/graphql"

    query = """
    query recentSubmissions($username: String!) {
        recentSubmissionList(username: $username) {
            title
            titleSlug
            timestamp
            statusDisplay
            lang
        }
    }
    """

    payload = {
        "query": query,
        "variables": {
            "username": "Fenriswolf200"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com",
        "Origin": "https://leetcode.com",
        "User-Agent": "Mozilla/5.0"
    }

    session = requests.Session()

    response = session.post(
        url,
        json=payload,
        headers=headers
    )

    print("STATUS:", response.status_code)
    print(response.text)

    return response.json()


get_leetcode_player_submissions()