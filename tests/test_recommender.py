import pytest

from src.recommender import Song, UserProfile, Recommender, recommend_songs

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def make_evaluation_songs():
    return [
        {
            "id": 1,
            "title": "Bright Pop Test",
            "artist": "Test Artist",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.85,
            "tempo_bpm": 122.0,
            "valence": 0.9,
            "danceability": 0.85,
            "acousticness": 0.1,
        },
        {
            "id": 2,
            "title": "Quiet Folk Test",
            "artist": "Test Artist",
            "genre": "folk",
            "mood": "sad",
            "energy": 0.25,
            "tempo_bpm": 70.0,
            "valence": 0.25,
            "danceability": 0.3,
            "acousticness": 0.9,
        },
        ,
        {
            "id": 4,
            "title": "Latin Dance Test",
            "artist": "Test Artist",
            "genre": "reggaeton",
            "mood": "happy",
            "energy": 0.8,
            "tempo_bpm": 96.0,
            "valence": 0.88,
            "danceability": 0.95,
            "acousticness": 0.08,
        },
        {
            "id": 5,
            "title": "Peaceful Jazz Test",
            "artist": "Test Artist",
            "genre": "jazz",
            "mood": "peaceful",
            "energy": 0.05,
            "tempo_bpm": 65.0,
            "valence": 0.6,
            "danceability": 0.35,
            "acousticness": 0.85,
        },
        {
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
        },
    ]


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


@pytest.mark.parametrize(
    ("user_prefs", "expected_title"),
    [
        (
            {
                "genre": "pop",
                "mood": "happy",
                "energy": 0.85,
                "likes_acoustic": False,
            },
            "Bright Pop Test",
        ),
        (
            {
                "genre": "folk",
                "mood": "sad",
                "energy": 0.25,
                "likes_acoustic": True,
            },
            "Quiet Folk Test",
        ),
        (
            {
                "genre": "lofi",
                "mood": "relaxed",
                "energy": 0.35,
                "likes_acoustic": True,
            },
            "Study Lofi Test",
        ),
        (
            {
                "genre": "reggaeton",
                "mood": "happy",
                "energy": 0.8,
                "likes_acoustic": False,
            },
            "Latin Dance Test",
        ),
    ],
)
def test_system_evaluation_profiles_return_expected_top_song(user_prefs, expected_title):
    songs = make_evaluation_songs()

    recommendations = recommend_songs(user_prefs, songs, k=3)

    assert recommendations[0][0]["title"] == expected_title
    assert recommendations[0][1] >= recommendations[1][1]
    assert recommendations[0][2].strip() != ""


def test_adversarial_unknown_genre_still_returns_ranked_results():
    user_prefs = {
        "genre": "made-up-genre",
        "mood": "happy",
        "energy": 0.8,
        "likes_acoustic": False,
    }
    songs = make_evaluation_songs()

    recommendations = recommend_songs(user_prefs, songs, k=3)

    assert len(recommendations) == 3
    assert recommendations[0][1] >= recommendations[1][1] >= recommendations[2][1]
    assert recommendations[0][0]["mood"] == "happy"


def test_edge_case_extreme_low_energy_prefers_calm_song():
    user_prefs = {
        "genre": "jazz",
        "mood": "peaceful",
        "energy": 0.0,
        "likes_acoustic": True,
    }
    songs = make_evaluation_songs()

    recommendations = recommend_songs(user_prefs, songs, k=1)

    assert recommendations[0][0]["title"] == "Peaceful Jazz Test"
    assert recommendations[0][0]["energy"] <= 0.1


def test_edge_case_extreme_high_energy_prefers_intense_song():
    user_prefs = {
        "genre": "rock",
        "mood": "intense",
        "energy": 1.0,
        "likes_acoustic": False,
    }
    songs = make_evaluation_songs()

    recommendations = recommend_songs(user_prefs, songs, k=1)

    assert recommendations[0][0]["title"] == "Intense Rock Test"
    assert recommendations[0][0]["energy"] >= 0.95
