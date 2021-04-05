import praw 
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logging.basicConfig(format   = '%(asctime)s  %(levelname)-8s %(message)s',
                    datefmt  = '%m-%d-%y %H:%M:%S',
                    filename = 'history.log',
                    filemode = 'a')
#Creating an object 
logger=logging.getLogger() 
#Setting the threshold of logger to DEBUG 
logger.setLevel(logging.INFO)


# reddit stuff 
reddit = praw.Reddit('bias_bot')

class BiasBot:
    def __init__(self,comment,username,keyword):
        self.keyword = keyword
        self.username = username
        self.totals = [0,0] # Posts, Comments
        self.data = self.get_posts()
        self.scores = self.analysis() # neg,neut,pos
        self.send_results(comment)

    # Collect posts and comments containing keyword and returns them in a list
    def get_posts(self) -> list():
        title_list = []

        try:
            for submission in reddit.redditor(self.username).submissions.new(limit=None):
                if submission.title.lower().find(self.keyword) > 0:
                    self.totals[0] += 1
                    title_list.append(submission.title)
            for comment in reddit.redditor(self.username).comments.new(limit=None):
                if comment.body.lower().find(self.keyword) > 0:
                    self.totals[1] += 1
                    title_list.append(comment.body) 
        except:
            logger.error("ERROR - Something went wrong with praw.")
            return
        return title_list

    # runs analysis on self.data and return totals in list [negative,neutral,positive]
    def analysis(self) -> list():
        results = [0,0,0] # neg,neut,pos
        sid = SentimentIntensityAnalyzer()
        for text in self.data:
            sentimentResults = sid.polarity_scores(text)
            score = sentimentResults["compound"]
            if(abs(score)) < 0.05:
                results[1] += 1
            elif(score) < 0 :
                results[0] += 1
            else:
                results[2] += 1 
        return results 

    def send_results(self,comment) -> None:
        logger.info(f"{self.username}, {self.keyword}, {self.totals[0]}/{self.totals[1]}, {self.scores[0]}/{self.scores[1]}/{self.scores[2]}")     
        print('Debug - Sending results')
        comment.reply(f"""{self.username} mentions {self.keyword} in {self.totals[0]} posts and {self.totals[1]} comments.
        
        Sentiment of relevant posts and comments:
        Negative: {self.scores[0]}
        Neutral: {self.scores[1]}
        Positive: {self.scores[2]}
        """)

def listener(trigger:str) -> None:
    print('Biasbot Active')
    print(f'Listening for trigger {trigger}:')
    while True:
        for comment in reddit.subreddit("all").stream.comments(skip_existing=True):
            if comment.body.lower().find(trigger) >= 0:  
                parse = comment.body.split(' ')
                for i in range(len(parse)):
                    if parse[i] == trigger and i+1 < len(parse):
                        keyword = parse[i+1]
                        try:
                            parent_author = comment.parent().author
                        except:
                            parent_author = comment.submission.author


                        # TODO spin into thread
                        print(comment,keyword)
                        BiasBot(comment,str(parent_author),keyword)

if __name__ == "__main__":
    listener('!biasbot')