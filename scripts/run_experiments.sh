#!/usr/bin/env sh
# Experiment plan, one factor at a time on the fixed 20% sample (plan 16.1).
# Run inside spark-client:  docker compose exec spark-client sh scripts/run_experiments.sh <step>
# Steps are separate because each one's best setting feeds the next.
set -e
T="spark-submit src/model/train.py"
NO_SW="preprocessing.use_domain_stopwords=false"
SW="preprocessing.use_domain_stopwords=true"

case "$1" in
  baseline)   # Bước 1 – basic stopwords, unigram, k=10
    $T --model kmeans --k 10 --exp Baseline --set $NO_SW
    $T --model lda    --k 10 --exp Baseline --set $NO_SW ;;
  exp1)       # Bước 2 – domain stopwords
    $T --model kmeans --k 10 --exp Exp1 --set $SW
    $T --model lda    --k 10 --exp Exp1 --set $SW ;;
  exp6)       # Cải tiến biểu diễn – Word2Vec + KMeans, vì TF-IDF + KMeans sụp trên bài ngắn
    $T --model w2v_kmeans --k ${2:-10} --exp Exp6 --set $SW ;;
  exp3)       # Bước 3 – number of topics for the models still in the race ($2: models)
    for m in ${2:-w2v_kmeans lda}; do
      for k in 5 8 15 20; do
        $T --model $m --k $k --exp Exp3 --set $SW
      done
    done ;;
  exp4)       # Bước 4 – BisectingKMeans at the best k ($2)
    $T --model bkm --k ${2:-10} --exp Exp4 --set preprocessing.use_domain_stopwords=${3:-true} ;;
  exp2)       # Bước 5 – bigrams with the best configuration ($2 model, $3 k)
    $T --model ${2:-kmeans} --k ${3:-10} --exp Exp2 \
       --set preprocessing.use_domain_stopwords=true preprocessing.use_bigram=true ;;
  final)      # Mô hình cuối trên toàn bộ dữ liệu ($2 model, $3 k)
    $T --model ${2:-kmeans} --k ${3:-10} --exp Final --data full --save --set $SW ;;
  *) echo "usage: run_experiments.sh baseline|exp1|exp6 [k]|exp3 [models]|exp4 [k] [sw]|exp2 [model] [k]|final [model] [k]"; exit 1 ;;
esac
