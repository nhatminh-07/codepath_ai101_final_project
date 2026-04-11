"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()

# main type of songs storage:
# It will be stored through a CSV file, which will be 
# represented by the main.py file and the songs.csv 
# (not including the actual music itself). The CSV file 
# will contain metadata about each song, such as title, 
# artist, genre, mood, energy level, and other relevant 
# attributes. The load_songs function in recommender.py 
# will read this CSV file and convert it into a list of 
# dictionaries or a similar data structure for easy access 
# and manipulation when scoring and recommending songs based 
# on user preferences.
#
#
# Weights
# There will be a regression problem within the Scoring Rule:
# score = w1 * genre_match + w2 * mood_match + w3 * energy_match + ...
# The weights (w1, w2, w3, etc.) will be determined through
# experimentation and tuning. Initially, you can start with 
# equal weights (e.g., w1 = w2 = w3 = 1) and then adjust them 
# based on the performance of your recommender system. You can
#  use techniques like grid search or random search to find 
# the optimal weights that maximize the relevance of the 
# recommended songs to the user's preferences.
