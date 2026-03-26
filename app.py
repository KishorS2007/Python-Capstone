import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("Movie Analytics Dashboard")


# Load and Prepare Data
@st.cache_data
def load_data():
    movies = pd.read_csv("movies.csv")
    ratings = pd.read_csv("ratings.csv")

    df = pd.merge(ratings, movies, on="movieId")

    movie_stats = df.groupby(["movieId", "title", "genres"]).agg(
        rating=("rating", "mean"),
        votes=("rating", "count")
    ).reset_index()

    movie_stats["genres"] = movie_stats["genres"].str.split("|")

    unwanted = {"IMAX", "(no genres listed)"}
    movie_stats["genres"] = movie_stats["genres"].apply(
        lambda x: [g for g in x if g not in unwanted]
    )

    return movie_stats


df = load_data()



# Weighted Rating   
C = df["rating"].mean()
m = df["votes"].quantile(0.75)

df["weighted_rating"] = (
    (df["votes"] / (df["votes"] + m)) * df["rating"] +
    (m / (df["votes"] + m)) * C
)


# Sidebar Filters
st.sidebar.header("Filters")

all_genres = sorted(set(g for sublist in df["genres"] for g in sublist))

search_movie = st.sidebar.text_input("Search Movie by Name")

selected_genres = st.sidebar.multiselect("Select Genre", all_genres,default=[],disabled=bool(search_movie))

rating_range = st.sidebar.slider(
    "Rating Range",
    float(df["rating"].min()),
    float(df["rating"].max()),
    (0.0, 5.0)
)



#  SEARCH (OVERRIDES EVERYTHING)
if search_movie:
    st.subheader(f"Search Results for: {search_movie}")
    selected_genres = []
    search_results = df[
        df["title"].str.contains(search_movie, case=False, na=False)
    ]

    if not search_results.empty:
        selected_movie = search_results.iloc[0]

        # Movie Details
        st.markdown("## Movie Details")

        col1, col2 = st.columns(2)

        col1.write(f"**Title:** {selected_movie['title']}")
        col1.write(f"**Genres:** {', '.join(selected_movie['genres'])}")

        col2.write(f"**Average Rating:** {round(selected_movie['rating'], 2)} ⭐")
        col2.write(f"**Votes:** {selected_movie['votes']}")
        col2.write(f"**Weighted Rating:** {round(selected_movie['weighted_rating'], 2)}")

        # show similar movies (same genre)
        st.markdown("### Similar Movies")

        similar_movies = df[
            df["genres"].apply(
                lambda x: any(g in x for g in selected_movie["genres"])
            )
        ]

        similar_movies = similar_movies.sort_values(
            by="weighted_rating",
            ascending=False
        ).head(5)

        st.dataframe(
            similar_movies[["title", "rating", "votes", "weighted_rating"]]
        )

    else:
        st.warning("No movie found with that name")

    #STOP execution
    st.stop()


#=================================================================

# Apply filters
filtered_df = df.copy()

if selected_genres:
    filtered_df = filtered_df[
        filtered_df["genres"].apply(
            lambda x: any(g in x for g in selected_genres)
        )
    ]

filtered_df = filtered_df[
    (filtered_df["rating"] >= rating_range[0]) &
    (filtered_df["rating"] <= rating_range[1])
]


# Metrics
col1, col2, col3 = st.columns(3)

col1.metric("Total Movies", len(filtered_df))
col2.metric(
    "Average Rating",
    round(filtered_df["rating"].mean(), 2) if not filtered_df.empty else 0
)
col3.metric(
    "Average Votes",
    int(filtered_df["votes"].mean()) if not filtered_df.empty else 0
)


# Top 10 Movies
st.subheader("Top 10 Movies")

if not filtered_df.empty:
    top10 = filtered_df.sort_values(
        by="weighted_rating",
        ascending=False
    ).head(10)

    fig, ax = plt.subplots()
    ax.barh(top10["title"], top10["weighted_rating"])
    ax.invert_yaxis()
    st.pyplot(fig)
else:
    st.warning("No data available")


# Top 5 per Genre
st.subheader("Top 5 Movies per Selected Genre")

if selected_genres:
    for genre in selected_genres:
        st.markdown(f"### {genre}")

        genre_df = df[
            df["genres"].apply(lambda x: genre in x)
        ]

        genre_df = genre_df[
            (genre_df["rating"] >= rating_range[0]) &
            (genre_df["rating"] <= rating_range[1])
        ]

        top5 = genre_df.sort_values(
            by="weighted_rating",
            ascending=False
        ).head(5)

        if not top5.empty:
            fig, ax = plt.subplots()
            ax.barh(top5["title"], top5["weighted_rating"])
            ax.invert_yaxis()
            st.pyplot(fig)
        else:
            st.write("No movies found")
else:
    st.info("Select at least one genre")


# Conclusion
st.subheader("Conclusion")

if not filtered_df.empty:
    genre_exploded = filtered_df.explode("genres")

    genre_stats = genre_exploded.groupby("genres").agg(
        avg_rating=("rating", "mean"),
        avg_votes=("votes", "mean")
    )

    genre_stats = genre_stats[genre_stats["avg_votes"] > m]

    if not genre_stats.empty:
        top_genre = genre_stats["avg_rating"].idxmax()

        st.success(
            f"{top_genre} movies offer the best combination of high ratings and strong audience support.\n\n"
            f"Recommended starting point for your next watch."
        )
    else:
        st.info("Not enough data")