Spin up server:
>bash run.py

Run metrics_analyzer:
>gcc metrics_analyzer.c -o metrics_analyzer $(pkg-config --cflags --libs jansson libcurl)
>./metrics_analyzer