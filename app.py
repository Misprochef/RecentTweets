import tweepy
import pandas as pd
from flask import Flask, render_template, request, logging, Response, redirect, flash
from config import CONFIG

CONSUMER_KEY = CONFIG["CONSUMER_KEY"]
CONSUMER_SECRET = CONFIG["CONSUMER_SECRET"]
ACCESS_TOKEN = CONFIG["ACCESS_TOKEN"]
ACCESS_SECRET = CONFIG["ACCESS_SECRET"]

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

api = tweepy.API(auth)

app = Flask(__name__)

columns = ["tweet_id", "created_at", "text", "fav", "retweets"]


@app.route("/")
def input():
    return render_template("input.html")


@app.route("/output", methods=["POST"])
def output():
    user_id = request.form["user_id"]
    tweets_df = get_tweets_df(user_id)
    grouped_df = get_grouped_df(tweets_df)
    sorted_df = get_sorted_df(tweets_df)
    profile = get_profile(user_id)
    max_of_retweets = max_of_ret(tweets_df)
    return render_template(
        "output.html",
        profile=profile,
        tweets_df=tweets_df,
        grouped_df=grouped_df,
        sorted_df=sorted_df,
        user_id=user_id,
        max_of_retweets=max_of_retweets,
    )


def get_tweets_df(user_id):
    tweets_df = pd.DataFrame(columns=columns)
    for tweet in tweepy.Cursor(
        api.user_timeline, screen_name=user_id, exclude_replies=True
    ).items(30):
        try:
            if not "RT @" in tweet.text:
                tweet_text = tweet.text.replace("\n", "")
                tweet_text_no_http = tweet_text.split("http")[0]
                se = pd.Series(
                    [
                        tweet.id,
                        tweet.created_at,
                        tweet_text_no_http,
                        tweet.favorite_count,
                        tweet.retweet_count,
                    ],
                    columns,
                )
                tweets_df = tweets_df.append(se, ignore_index=True)
        except Exception as e:
            print(e)
    tweets_df["created_at"] = pd.to_datetime(tweets_df["created_at"])
    return tweets_df


def get_profile(user_id):
    user = api.get_user(screen_name=user_id)
    profile = {
        "user_id": user_id,
        "image": user.profile_image_url,
        "description": user.description,
        "homepage": user.url,
    }
    return profile


def get_grouped_df(tweets_df):
    grouped_df = (
        tweets_df.groupby(tweets_df.created_at.dt.date)
        .sum()
        .sort_values(by="created_at", ascending=False)
    )
    return grouped_df


def get_sorted_df(tweets_df):
    sorted_df = tweets_df.sort_values(by="retweets", ascending=False)
    return sorted_df


def max_of_ret(tweets_df):
    max_ret_value = int(
        tweets_df.sort_values(by="retweets", ascending=False).iloc[0]["retweets"]
    )
    return max_ret_value


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)

