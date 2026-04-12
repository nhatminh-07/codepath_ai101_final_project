# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder 1.0 is designed to recommend songs from a CSV catalog based on a simple user profile. It returns the top 5 songs that best match the user's selected genre, mood, target energy, and acoustic preference.

This project is intended for learning and experimentation. It is not meant to replace professional music recommendation systems used by large streaming platforms.

---

## 3. How the Model Works

This system is a beginner-friendly rule-based recommender. It does not train on user history or learn from large datasets. Instead, it uses human-written scoring rules to compare each song with the user's preferences.

The model uses these song features:

- Genre
- Mood
- Energy
- Acousticness

The current scoring logic works like this:

- Add 2 points when the song genre exactly matches the user's preferred genre.
- Add 2 points when the song mood exactly matches the user's preferred mood.
- Add up to 1 point when the song energy is close to the user's target energy.
- Add up to 1 point based on whether the user prefers acoustic or less acoustic
  music.

After every song is scored, the system sorts the songs from highest score to
lowest score and returns the top results with short explanations.

---

## 4. Data

The recommender uses the dataset in `data/songs.csv`. The dataset contains 340 songs with metadata such as title, artist, genre, mood, energy, tempo, valence, danceability, and acousticness.

Example genres include rock, pop, V-pop, K-pop, hip hop, synth pop, soul, funk, jazz, disco, electronic music, alternative rock, and indie rock.

---

## 5. Strengths

The main strength of this system is that it is easy to understand and explain. Because the rules are visible in the code, users can see why a song was recommended. This makes the project useful for learning how recommender systems use features, weights, ranking, and explanations.

The system can produce reasonable results when a user's preferences are simple, such as wanting happy pop songs, calm acoustic songs, or high-energy music.

---

## 6. Limitations and Bias

The system can create filter bubbles because it gives large bonuses for exact genre and mood matches. For example, if a user says they like pop music, the system may keep recommending pop songs and ignore nearby genres that could also fit the user's taste.

The model also treats labels as exact matches. This means `pop`, `v-pop`, and `synth pop` are handled as separate genres even though they may be related. A more advanced system could use genre similarity, word embeddings, or grouped genre families to make softer comparisons.

The current scoring logic may not fully represent users who care about features like danceability, tempo, or valence. For example, a Dance / Party Listener may care more about tempo and danceability than genre, but those features are not currently part of the score.

The energy score is based on distance from the user's target energy. This works for simple cases, but genre and mood bonuses can overpower energy. As a result, a song with the right genre and mood could rank above a song with a better energy match.

The system does not learn from skips, likes, playlists, listening history, or changes in taste over time.

---

## 7. Evaluation

The system was evaluated with several user profiles from the README, including normal use cases, adversarial cases, and edge cases.

Tested profiles included:

- Energetic Pop Listener: expects happy, high-energy pop songs.
- Sad Acoustic Listener: expects lower-energy acoustic songs.
- Chill Study Listener: expects relaxed, medium-low energy songs.
- Latin Dance Listener: expects energetic, less acoustic dance songs.
- Unknown Genre User: tests whether the system still works when the genre does
  not exist in the dataset.
- Extreme Low Energy User: tests whether the system can recommend very calm
  songs.
- Extreme High Energy User: tests whether the system can recommend very intense
  songs.

The tests checked whether the highest-ranked songs matched the expected genre, mood, energy level, and acoustic preference. The tests also checked that the system returns readable explanations and does not crash on unusual inputs.

---

## 8. Future Work

Some improvements I could make in the future include:

- Add more data and more song features, such as tempo, valence, danceability, language, region, and popularity.
- Add more scoring factors so the system can reward both exact matches and close matches.
- Fine-tune the scoring weights after testing the recommender with different user profiles.
- Improve genre and mood matching by representing them as vectors instead of exact words. This would let the system understand that related genres, such as  `pop`, `v-pop`, and `synth pop`, have shared meanings.
- Add diversity rules so the top results do not all come from the same genre, mood, or artist.

In a larger real-world system, these improvements could be learned from user data, but this project keeps the logic rule-based so it remains easier to understand.

---

## 9. Personal Reflection

This project taught me how recommendation systems turn simple rules into ranked results. It also helped me understand how a basic rule-based system is connected to the history of AI, especially earlier symbolic AI systems from the 1960s and 1970s.

I learned that recommendation systems are not only technical systems. They also shape what people see, hear, and discover. Even a simple music recommender can create bias if it repeats the same genres or moods too often. This connects to larger concerns about platform economies, filter bubbles, and echo chambers in modern recommendation systems.

The most important thing I learned is that the design of the scoring rules matters. Small choices, such as giving extra points for exact genre matches, can change the recommendations a lot.
