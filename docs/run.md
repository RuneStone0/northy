
cd RuneStone0/northy
git pull

## Start job: Monitor Northy Tweets
```
screen -S tweets
source venv/bin/activate
cli_tweets.py watch
```

## Start job: Parse alert signals
```
screen -S signals
source venv/bin/activate
cli_signal.py watch
```

## Start job: Saxo trader
```
screen -S saxo
source venv/bin/activate
cli_saxo.py watch
```

