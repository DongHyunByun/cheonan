docker run -it -v $(pwd)/data_before:/cheonan/data_before -v $(pwd)/data_after:/cheonan/data_after -v $(pwd)/do_not_remove:/cheonan/do_not_remove --rm dgoodsamari/cheonan:0.1 python main.py --type "인구지표"
