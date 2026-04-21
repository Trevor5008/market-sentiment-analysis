## What We Found

We analyzed roughly **84,000 news articles** and linked them to **two years of stock market data** for major tech companies. From that, we built a set of simple signals based on three things:

- recent price movement  
- trading activity  
- news sentiment  

These signals showed a **weak signal** with stock performance, especially when used together.

## What Actually Worked

The clearest pattern was not in predicting whether a stock would simply go **up or down**. The model was better at answering a different question:

> **Which stocks are likely to perform better than others?**

That distinction mattered.

Out of all the signals we tested, **recent price movement** was the strongest. It consistently carried more predictive value than the news-based features. When the combined signal was strong, average returns were noticeably better—about **0.6% to 0.8% higher per day** than weak-signal cases.

## What Did *Not* Change the Outcome Much

We also spent time improving the data and testing more sophisticated approaches.

Cleaning errors out of the dataset made the results **more credible and more stable**, but it did **not meaningfully improve performance**. The same thing happened when we added more advanced features and more complex models: the gains were small, and the overall results stayed roughly the same.

The project was not being held back by one obvious issue.

## Bottom Line

There does appear to be a **small, persistent signal** in the data. It survived across time and did not vanish after cleanup, which suggests the signal is real.

But it was also **too weak to meet the target**.

The final takeaway is simple:

> We found a signal worth noticing, but not one strong enough to trust for confident trading predictions.