"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from .recommender import load_songs, recommend_songs
except ImportError:
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    #user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    user_prefs = {
            "id": 6,
            "title": "Intense Rock Test",
            "artist": "Test Artist",
            "genre": "rock",
            "mood": "intense",
            "energy": 0.98,
            "tempo_bpm": 150.0,
            "valence": 0.65,
            "danceability": 0.7,
            "acousticness": 0.05,
        }
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations")
    print("===================")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n{rank}. {song['title']} by {song['artist']}")
        print(f"   Score: {score:.2f}")
        print(f"   Reasons: {explanation}")


if __name__ == "__main__":
    main()


