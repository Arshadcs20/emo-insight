import csv
import pathlib
from instaloader import Instaloader, Post
import emoji

# Initialize Instaloader
# bot = Instaloader()

# Login to Instagram (not recommended for scraping purposes)
# bot.login(user="marshadcs20", passwd="marshadcs20-24")


def scrape_instagram_comments(url):
    # Example URL to scrape comments from
    # url = "https://www.instagram.com/p/C4Dujzgi5v3/"

    # Get post object from URL
    # post = Post.from_shortcode(bot.context, url[28:-1])
    # Initialize Instaloader
    bot = Instaloader()
    bot.login(user="marshadcs20", passwd="marshadcs20-24")
    # Get post object from URL
    post = Post.from_shortcode(bot.context, url[28:-1])

    comment_texts = []

    # Iterate through the comments and store comment texts in an array
    for comment in post.get_comments():
        comment_texts.append(emoji.demojize(comment.text)
                             if comment.text else "")

    return comment_texts

# Create the CSV file
# csvName = post.shortcode + '.csv'
# output_path = pathlib.Path('post_data')
# post_file = output_path.joinpath(csvName).open(
#     "w", encoding="utf-8", newline="")

# # Write the header row
# field_names = [
#     "post_shortcode",
#     "commenter_username",
#     "comment_text",
#     "comment_likes"
# ]
# # post_writer = csv.DictWriter(post_file, fieldnames=field_names)
# post_writer.writeheader()

# comment_texts = []
# Iterate through the comments and write them to the CSV file
# for comment in post.get_comments():
    # post_info = {
    #     "post_shortcode": post.shortcode,
    #     "commenter_username": comment.owner.username,
    #     "comment_text": emoji.demojize(comment.text) if comment.text else "",
    #     "comment_likes": comment.likes_count
    # }
    # post_writer.writerow(post_info)
    # comment_texts.append(emoji.demojize(comment.text) if comment.text else "")

# Close the CSV file
# post_file.close()

# Print a success message
# print("Done Scraping!")
# print(comment_texts)
