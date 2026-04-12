import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        return sorted(
            self.songs,
            key=lambda song: score_song(user_prefs, song.__dict__),
            reverse=True,
        )[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        user_prefs = {
            "favorite_genre": user.favorite_genre,
            "favorite_mood": user.favorite_mood,
            "target_energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        return explain_song(user_prefs, song.__dict__)

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    numeric_fields = {
        "energy",
        "tempo_bpm",
        "valence",
        "danceability",
        "acousticness",
    }

    songs: List[Dict] = []

    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)

        for row_number, row in enumerate(reader, start=2):
            try:
                song = dict(row)
                song["id"] = int(song["id"])

                for field in numeric_fields:
                    song[field] = float(song[field])

                songs.append(song)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid song data in {csv_path} on row {row_number}: {row}"
                ) from exc

    return songs

def score_song(user_prefs: Dict, song: Dict) -> float:
    """
    Scores a single song based on user preferences.
    Required by src/main.py
    """
    score = 0.0

    preferred_genre = user_prefs.get("genre") or user_prefs.get("favorite_genre")
    if preferred_genre and song.get("genre") == preferred_genre:
        score += 2.0

    preferred_mood = user_prefs.get("mood") or user_prefs.get("favorite_mood")
    if preferred_mood and song.get("mood") == preferred_mood:
        score += 2.0

    target_energy = user_prefs.get("energy", user_prefs.get("target_energy"))
    if target_energy is not None:
        score += 1.0 - abs(float(song.get("energy", 0.0)) - float(target_energy))

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        acousticness = float(song.get("acousticness", 0.0))
        score += acousticness if likes_acoustic else 1.0 - acousticness

    return score

def explain_song(user_prefs: Dict, song: Dict) -> str:
    """
    Explains why a song was recommended.
    """
    reasons = []

    preferred_genre = user_prefs.get("genre") or user_prefs.get("favorite_genre")
    if preferred_genre and song.get("genre") == preferred_genre:
        reasons.append(f"matches your preferred genre ({preferred_genre})")

    preferred_mood = user_prefs.get("mood") or user_prefs.get("favorite_mood")
    if preferred_mood and song.get("mood") == preferred_mood:
        reasons.append(f"matches your preferred mood ({preferred_mood})")

    target_energy = user_prefs.get("energy", user_prefs.get("target_energy"))
    if target_energy is not None:
        energy = float(song.get("energy", 0.0))
        if abs(energy - float(target_energy)) <= 0.15:
            reasons.append("has energy close to your target")

    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is True and float(song.get("acousticness", 0.0)) >= 0.6:
        reasons.append("has an acoustic sound")
    elif likes_acoustic is False and float(song.get("acousticness", 0.0)) <= 0.4:
        reasons.append("has a less acoustic sound")

    if not reasons:
        return "This song has the closest overall match to your preferences."

    return "This song " + ", ".join(reasons) + "."

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """
    scored_songs = [
        (song, score_song(user_prefs, song), explain_song(user_prefs, song))
        for song in songs
    ]
    scored_songs.sort(key=lambda item: item[1], reverse=True)
    return scored_songs[:k]


